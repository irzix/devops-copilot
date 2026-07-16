from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional


class HealthCheck(SQLModel, table=True):
    """Stores periodic health check results for each managed server."""

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id", index=True, nullable=False)
    status: str = Field(nullable=False)  # "healthy", "degraded", "unreachable"

    cpu_percent: Optional[float] = Field(default=None)
    memory_percent: Optional[float] = Field(default=None)
    disk_percent: Optional[float] = Field(default=None)
    response_time_ms: Optional[int] = Field(default=None)
    error_message: Optional[str] = Field(default=None)

    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class MonitoringSettings(SQLModel, table=True):
    """Per-user configurable monitoring preferences."""

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", unique=True, nullable=False)

    # How often to run health checks (seconds)
    check_interval: int = Field(default=300)  # 5 minutes

    # Alert thresholds (percentage)
    cpu_threshold: float = Field(default=90.0)
    memory_threshold: float = Field(default=85.0)
    disk_threshold: float = Field(default=90.0)

    # Master switch
    is_enabled: bool = Field(default=True)
