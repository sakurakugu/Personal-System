"""Admin system status route (psutil)."""

from __future__ import annotations

import time

import psutil
from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.models.models import User
from app.schemas.schemas import SystemStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system", response_model=SystemStatus)
async def system_status(_admin: User = Depends(require_admin)):
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return SystemStatus(
        cpu_percent=psutil.cpu_percent(interval=0.5),
        memory_total_gb=round(mem.total / (1024 ** 3), 2),
        memory_used_gb=round(mem.used / (1024 ** 3), 2),
        memory_percent=mem.percent,
        disk_total_gb=round(disk.total / (1024 ** 3), 2),
        disk_used_gb=round(disk.used / (1024 ** 3), 2),
        disk_percent=disk.percent,
        uptime_seconds=round(time.time() - psutil.boot_time(), 1),
    )
