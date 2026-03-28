"""后台管理服务。"""

from __future__ import annotations

import time

import psutil
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_MIN_ROLE,
    SYSTEM_SETTING_COMMENTS_STEALTH,
    SYSTEM_SETTING_REGISTER_ENABLED,
    SystemSetting,
)
from app.schemas.system import SystemSettingsRead, SystemSettingsUpdate, SystemStatus

psutil.cpu_percent(interval=None)

_cached_status: SystemStatus | None = None
_cached_at = 0.0
_CACHE_TTL_SECONDS = 2.0
_VALID_COMMENT_ROLES = {"guest", "user", "admin", "super_admin"}


async def _get_bool_setting(db: AsyncSession, key: str, default: bool) -> bool:
    """从数据库读取布尔设置。"""
    setting = await db.get(SystemSetting, key)
    if setting is None or setting.bool_value is None:
        return default
    return setting.bool_value


async def _get_str_setting(db: AsyncSession, key: str, default: str) -> str:
    """从数据库读取字符串设置。"""
    setting = await db.get(SystemSetting, key)
    if setting is None or setting.str_value is None:
        return default
    return setting.str_value


async def _set_bool_setting(db: AsyncSession, key: str, value: bool) -> None:
    """写入布尔设置。"""
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=value, str_value=None)
        db.add(setting)
    else:
        setting.bool_value = value
    await db.flush()


async def _set_str_setting(db: AsyncSession, key: str, value: str) -> None:
    """写入字符串设置。"""
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=None, str_value=value)
        db.add(setting)
    else:
        setting.str_value = value
    await db.flush()


def validate_comments_min_role(value: str) -> str:
    """校验评论最低角色设置。"""
    if value not in _VALID_COMMENT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {sorted(_VALID_COMMENT_ROLES)}",
        )
    return value


async def read_system_settings(db: AsyncSession) -> SystemSettingsRead:
    """读取全部系统设置。"""
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


def get_system_status() -> SystemStatus:
    """获取系统状态，并做短时缓存。"""
    global _cached_status, _cached_at
    now = time.monotonic()
    if _cached_status is not None and now - _cached_at < _CACHE_TTL_SECONDS:
        return _cached_status

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    status = SystemStatus(
        cpu_percent=psutil.cpu_percent(interval=None),
        memory_total_gb=round(mem.total / (1024**3), 2),
        memory_used_gb=round(mem.used / (1024**3), 2),
        memory_percent=mem.percent,
        disk_total_gb=round(disk.total / (1024**3), 2),
        disk_used_gb=round(disk.used / (1024**3), 2),
        disk_percent=disk.percent,
        uptime_seconds=round(time.time() - psutil.boot_time(), 1),
    )
    _cached_status = status
    _cached_at = now
    return status


async def update_system_settings(db: AsyncSession, body: SystemSettingsUpdate) -> SystemSettingsRead:
    """更新系统设置。"""
    if body.comments_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, body.comments_enabled)
        if body.comments_enabled:
            await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_STEALTH, False)

    if body.comments_stealth is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_STEALTH, body.comments_stealth)
        if body.comments_stealth:
            await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, False)

    if body.comments_min_role is not None:
        await _set_str_setting(
            db,
            SYSTEM_SETTING_COMMENTS_MIN_ROLE,
            validate_comments_min_role(body.comments_min_role),
        )

    if body.register_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_REGISTER_ENABLED, body.register_enabled)

    return await read_system_settings(db)
