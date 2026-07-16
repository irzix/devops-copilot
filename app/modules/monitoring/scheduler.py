import time
import asyncio
import logging
from datetime import datetime, timezone

from sqlmodel import select
from filelock import FileLock, Timeout

from app.core.database import async_session_maker
from app.modules.servers.models import Server
from app.modules.monitoring.models import HealthCheck, MonitoringSettings
from app.modules.monitoring.service import probe_server

logger = logging.getLogger("monitoring.scheduler")

# In-memory map to track when a server was last checked
_last_checked_map: dict[int, float] = {}

# Global lock to ensure only one worker runs the loop
LOCK_FILE = "/tmp/monitoring_scheduler.lock"


async def health_check_loop():
    """Background task that periodically probes all servers."""
    await asyncio.sleep(5)  # Wait for app boot

    lock = FileLock(LOCK_FILE, timeout=0)
    try:
        lock.acquire()
    except Timeout:
        logger.info("Another worker is running the health check loop. Exiting this worker's loop.")
        return

    logger.info("Acquired scheduler lock. Starting health check loop.")
    try:
        while True:
            try:
                await _run_health_checks()
            except asyncio.CancelledError:
                logger.info("Health check loop cancelled.")
                return
            except Exception:
                logger.exception("Health check cycle failed")

            await asyncio.sleep(10)  # Main loop ticks every 10 seconds
    finally:
        lock.release()


async def _run_health_checks():
    """Run one cycle of health checks for servers that are due."""
    async with async_session_maker() as session:
        result = await session.exec(select(Server))
        servers = result.all()
        if not servers:
            return

        settings_result = await session.exec(select(MonitoringSettings))
        settings_map = {s.owner_id: s for s in settings_result.all()}

    now = time.time()
    due_servers = []

    for server in servers:
        # Check user settings
        user_settings = settings_map.get(server.owner_id)
        if user_settings and not user_settings.is_enabled:
            continue

        interval = user_settings.check_interval if user_settings else 300
        last_checked = _last_checked_map.get(server.id, 0)
        
        if (now - last_checked) >= interval:
            due_servers.append(server)
            _last_checked_map[server.id] = now

    if not due_servers:
        return

    # Probe due servers concurrently with a limit of 10
    sem = asyncio.Semaphore(10)
    
    async def _bounded_probe(srv):
        async with sem:
            return await probe_server(srv)

    results = await asyncio.gather(
        *[_bounded_probe(srv) for srv in due_servers],
        return_exceptions=True,
    )

    async with async_session_maker() as session:
        for server, probe_result in zip(due_servers, results):
            if isinstance(probe_result, Exception):
                health = HealthCheck(
                    server_id=server.id,
                    status="unreachable",
                    error_message=str(probe_result),
                    checked_at=datetime.now(timezone.utc),
                )
            else:
                user_settings = settings_map.get(server.owner_id)
                status = _evaluate_status(probe_result, user_settings)
                probe_result.status = status

                health = HealthCheck(
                    server_id=probe_result.server_id,
                    status=probe_result.status,
                    cpu_percent=probe_result.cpu_percent,
                    memory_percent=probe_result.memory_percent,
                    disk_percent=probe_result.disk_percent,
                    response_time_ms=probe_result.response_time_ms,
                    error_message=probe_result.error_message,
                    checked_at=datetime.now(timezone.utc),
                )

            session.add(health)

            if health.status != "healthy":
                try:
                    from app.modules.notifications.service import send_health_alert
                    await send_health_alert(server, health)
                except ImportError:
                    pass

        await session.commit()


def _evaluate_status(probe_result, settings: MonitoringSettings | None) -> str:
    """Compare probe metrics against user-configured thresholds."""
    if probe_result.status == "unreachable":
        return "unreachable"

    cpu_threshold = settings.cpu_threshold if settings else 90.0
    mem_threshold = settings.memory_threshold if settings else 85.0
    disk_threshold = settings.disk_threshold if settings else 90.0

    if (
        (probe_result.cpu_percent and probe_result.cpu_percent > cpu_threshold)
        or (probe_result.memory_percent and probe_result.memory_percent > mem_threshold)
        or (probe_result.disk_percent and probe_result.disk_percent > disk_threshold)
    ):
        return "degraded"

    return "healthy"
