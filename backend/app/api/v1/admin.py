"""管理系统状态路由（psutil）。"""

from __future__ import annotations

import time

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_super_admin
from app.core.database import get_db
from app.models.models import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_MIN_ROLE,
    SYSTEM_SETTING_COMMENTS_STEALTH,
    SYSTEM_SETTING_REGISTER_ENABLED,
    SystemSetting,
    User,
)
from app.schemas.schemas import SystemSettingsRead, SystemSettingsUpdate, SystemStatus

router = APIRouter(prefix="/admin", tags=["admin"])
psutil.cpu_percent(interval=None)
_cached_status: SystemStatus | None = None
_cached_at = 0.0
_CACHE_TTL_SECONDS = 2.0


async def _get_bool_setting(db: AsyncSession, key: str, default: bool) -> bool:
    setting = await db.get(SystemSetting, key)
    if setting is None or setting.bool_value is None:
        return default
    return setting.bool_value


async def _get_str_setting(db: AsyncSession, key: str, default: str) -> str:
    setting = await db.get(SystemSetting, key)
    if setting is None or setting.str_value is None:
        return default
    return setting.str_value


async def _set_bool_setting(db: AsyncSession, key: str, value: bool) -> None:
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=value, str_value=None)
        db.add(setting)
    else:
        setting.bool_value = value
    await db.flush()


async def _set_str_setting(db: AsyncSession, key: str, value: str) -> None:
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=None, str_value=value)
        db.add(setting)
    else:
        setting.str_value = value
    await db.flush()


async def _read_system_settings(db: AsyncSession) -> SystemSettingsRead:
    comments_enabled = await _get_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, True)
    comments_stealth = await _get_bool_setting(db, SYSTEM_SETTING_COMMENTS_STEALTH, False)
    comments_min_role = await _get_str_setting(db, SYSTEM_SETTING_COMMENTS_MIN_ROLE, "guest")
    register_enabled = await _get_bool_setting(db, SYSTEM_SETTING_REGISTER_ENABLED, True)
    return SystemSettingsRead(
        comments_enabled=comments_enabled,
        comments_stealth=comments_stealth,
        comments_min_role=comments_min_role,
        register_enabled=register_enabled,
    )


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


@router.get("/public-settings", response_model=SystemSettingsRead)
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    return await _read_system_settings(db)


@router.get("/settings", response_model=SystemSettingsRead)
async def get_settings(
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _read_system_settings(db)


@router.patch("/settings", response_model=SystemSettingsRead)
async def update_settings(
    body: SystemSettingsUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.comments_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, body.comments_enabled)
        if body.comments_enabled:
            await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_STEALTH, False)
    if body.comments_stealth is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_STEALTH, body.comments_stealth)
        if body.comments_stealth:
            await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, False)
    if body.comments_min_role is not None:
        # 验证角色值
        valid_roles = ["guest", "user", "admin", "super_admin"]
        if body.comments_min_role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
        await _set_str_setting(db, SYSTEM_SETTING_COMMENTS_MIN_ROLE, body.comments_min_role)
    if body.register_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_REGISTER_ENABLED, body.register_enabled)
    return await _read_system_settings(db)
