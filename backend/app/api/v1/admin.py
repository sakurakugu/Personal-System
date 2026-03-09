"""管理系统状态路由（psutil）。"""

from __future__ import annotations

import time

import psutil
from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.models.models import User
from app.schemas.schemas import SystemStatus

router = APIRouter(prefix="/admin", tags=["admin"])
psutil.cpu_percent(interval=None)
_cached_status: SystemStatus | None = None
_cached_at = 0.0
_CACHE_TTL_SECONDS = 2.0


@router.get("/system", response_model=SystemStatus)
async def system_status(_admin: User = Depends(require_admin)):
    global _cached_status, _cached_at
    now = time.monotonic()
    if _cached_status and now - _cached_at < _CACHE_TTL_SECONDS:
        return _cached_status
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    status = SystemStatus(
        cpu_percent=psutil.cpu_percent(interval=None),
        memory_total_gb=round(mem.total / (1024 ** 3), 2),
        memory_used_gb=round(mem.used / (1024 ** 3), 2),
        memory_percent=mem.percent,
        disk_total_gb=round(disk.total / (1024 ** 3), 2),
        disk_used_gb=round(disk.used / (1024 ** 3), 2),
        disk_percent=disk.percent,
        uptime_seconds=round(time.time() - psutil.boot_time(), 1),
    )
    _cached_status = status
    _cached_at = now
    return status
