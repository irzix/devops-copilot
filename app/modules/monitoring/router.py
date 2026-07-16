from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.modules.auth import User
from app.modules.auth.service import get_current_user
from app.modules.monitoring.service import (
    get_user_servers_health_status,
    get_server_health_history_for_user,
    get_user_monitoring_settings,
    update_user_monitoring_settings,
)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────


class HealthStatusResponse(BaseModel):
    server_id: int
    server_name: str
    status: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: Optional[str] = None

    class Config:
        from_attributes = True


class MonitoringSettingsUpdate(BaseModel):
    check_interval: Optional[int] = Field(None, ge=60, le=3600, description="Check interval in seconds (60-3600)")
    cpu_threshold: Optional[float] = Field(None, ge=1, le=100)
    memory_threshold: Optional[float] = Field(None, ge=1, le=100)
    disk_threshold: Optional[float] = Field(None, ge=1, le=100)
    is_enabled: Optional[bool] = None


class MonitoringSettingsResponse(BaseModel):
    check_interval: int
    cpu_threshold: float
    memory_threshold: float
    disk_threshold: float
    is_enabled: bool

    class Config:
        from_attributes = True


# ── Endpoints ────────────────────────────────────────────────


@router.get("/status", response_model=List[HealthStatusResponse])
async def get_health_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the latest health status for all servers owned by the current user."""
    results = await get_user_servers_health_status(session, current_user.id)
    return results


@router.get("/{server_id}/history", response_model=List[HealthStatusResponse])
async def get_server_health_history(
    server_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get health check history for a specific server."""
    results = await get_server_health_history_for_user(session, server_id, current_user.id, limit)
    if results is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return results


@router.get("/settings", response_model=MonitoringSettingsResponse)
async def get_monitoring_settings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the current user's monitoring settings."""
    settings = await get_user_monitoring_settings(session, current_user.id)
    return settings


@router.put("/settings", response_model=MonitoringSettingsResponse)
async def update_monitoring_settings(
    payload: MonitoringSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update monitoring interval, thresholds, and enable/disable monitoring."""
    updates = payload.model_dump(exclude_unset=True)
    settings = await update_user_monitoring_settings(session, current_user.id, updates)
    return settings
