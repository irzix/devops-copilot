import time
import asyncio
import asyncssh
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import decrypt_data
from app.modules.servers.models import Server
from app.modules.monitoring.models import HealthCheck, MonitoringSettings


@dataclass
class HealthResult:
    """Parsed health probe output."""

    server_id: int
    server_name: str
    status: str  # "healthy", "degraded", "unreachable"
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None


# One-liner probe command: outputs CPU|MEM|DISK as parseable text
_PROBE_CMD = (
    'echo "CPU:$(top -bn1 2>/dev/null | grep -i "cpu" | head -1 '
    "| awk '{print $2}' | sed 's/%//')|"
    "MEM:$(free 2>/dev/null | awk '/Mem/{printf \"%.1f\", $3/$2*100}')|"
    'DISK:$(df / 2>/dev/null | awk \'NR==2{gsub(/%/,"",$5); print $5}\')"'
)


async def probe_server(server: Server) -> HealthResult:
    """SSH into a server, run a lightweight health probe, and parse the result."""
    start = time.monotonic()

    credential = decrypt_data(server.encrypted_credential)
    conn_args: dict = {
        "host": server.ip_address,
        "port": server.ssh_port,
        "username": server.ssh_username,
        "known_hosts": None,
    }

    if server.ssh_auth_type == "password":
        conn_args["password"] = credential
    else:
        try:
            conn_args["client_keys"] = [asyncssh.import_private_key(credential)]
        except Exception as e:
            return HealthResult(
                server_id=server.id,
                server_name=server.name,
                status="unreachable",
                error_message=f"Invalid SSH key: {e}",
            )

    try:
        async def _run():
            async with asyncssh.connect(**conn_args) as conn:
                result = await conn.run(_PROBE_CMD, check=False)
                return result.stdout or ""

        stdout = await asyncio.wait_for(_run(), timeout=15.0)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return _parse_probe_output(stdout, server, elapsed_ms)

    except asyncio.TimeoutError:
        return HealthResult(
            server_id=server.id,
            server_name=server.name,
            status="unreachable",
            response_time_ms=15000,
            error_message="SSH probe timed out after 15s",
        )
    except (asyncssh.Error, OSError) as e:
        return HealthResult(
            server_id=server.id,
            server_name=server.name,
            status="unreachable",
            error_message=str(e),
        )


def _parse_probe_output(
    stdout: str, server: Server, elapsed_ms: int
) -> HealthResult:
    """Parse the probe command output into structured metrics."""
    cpu = mem = disk = None

    try:
        for part in stdout.strip().split("|"):
            if part.startswith("CPU:"):
                val = part[4:].strip()
                if val:
                    cpu = float(val)
            elif part.startswith("MEM:"):
                val = part[4:].strip()
                if val:
                    mem = float(val)
            elif part.startswith("DISK:"):
                val = part[5:].strip()
                if val:
                    disk = float(val)
    except (ValueError, IndexError):
        pass  # Partial parse is fine — we still report what we got

    status = "healthy"
    # We'll compare against thresholds in the scheduler, not here
    if cpu is None and mem is None and disk is None:
        status = "degraded"  # Probe ran but couldn't parse metrics

    return HealthResult(
        server_id=server.id,
        server_name=server.name,
        status=status,
        cpu_percent=cpu,
        memory_percent=mem,
        disk_percent=disk,
        response_time_ms=elapsed_ms,
    )


# ── Database Service Operations ──────────────────────────────────────────────

async def get_user_servers_health_status(session: AsyncSession, user_id: int) -> list[dict]:
    """Get the latest health status for all servers owned by the given user."""
    servers_result = await session.exec(select(Server).where(Server.owner_id == user_id))
    servers = servers_result.all()

    if not servers:
        return []

    results = []
    for server in servers:
        hc_result = await session.exec(
            select(HealthCheck)
            .where(HealthCheck.server_id == server.id)
            .order_by(HealthCheck.checked_at.desc())
            .limit(1)
        )
        latest = hc_result.first()

        if latest:
            results.append({
                "server_id": server.id,
                "server_name": server.name,
                "status": latest.status,
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "disk_percent": latest.disk_percent,
                "response_time_ms": latest.response_time_ms,
                "error_message": latest.error_message,
                "checked_at": latest.checked_at.isoformat() if latest.checked_at else None,
            })
        else:
            results.append({
                "server_id": server.id,
                "server_name": server.name,
                "status": "unknown",
            })
    return results


async def get_server_health_history_for_user(
    session: AsyncSession, server_id: int, user_id: int, limit: int = 50
) -> list[dict] | None:
    """Get health check history for a specific server if owned by the user."""
    server_result = await session.exec(
        select(Server).where(Server.id == server_id, Server.owner_id == user_id)
    )
    server = server_result.first()
    if not server:
        return None  # Not found or not authorized

    hc_result = await session.exec(
        select(HealthCheck)
        .where(HealthCheck.server_id == server_id)
        .order_by(HealthCheck.checked_at.desc())
        .limit(limit)
    )
    checks = hc_result.all()

    return [
        {
            "server_id": server.id,
            "server_name": server.name,
            "status": hc.status,
            "cpu_percent": hc.cpu_percent,
            "memory_percent": hc.memory_percent,
            "disk_percent": hc.disk_percent,
            "response_time_ms": hc.response_time_ms,
            "error_message": hc.error_message,
            "checked_at": hc.checked_at.isoformat() if hc.checked_at else None,
        }
        for hc in checks
    ]


async def get_user_monitoring_settings(session: AsyncSession, user_id: int) -> MonitoringSettings:
    """Get the current user's monitoring settings, returning defaults if not set."""
    result = await session.exec(
        select(MonitoringSettings).where(MonitoringSettings.owner_id == user_id)
    )
    settings = result.first()

    if not settings:
        settings = MonitoringSettings(
            owner_id=user_id,
            check_interval=300,
            cpu_threshold=90.0,
            memory_threshold=85.0,
            disk_threshold=90.0,
            is_enabled=True,
        )
    return settings


async def update_user_monitoring_settings(
    session: AsyncSession, user_id: int, updates: dict
) -> MonitoringSettings:
    """Update monitoring settings for the user."""
    result = await session.exec(
        select(MonitoringSettings).where(MonitoringSettings.owner_id == user_id)
    )
    settings = result.first()

    if not settings:
        settings = MonitoringSettings(owner_id=user_id)

    for key, value in updates.items():
        if value is not None and hasattr(settings, key):
            setattr(settings, key, value)

    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings
