"""后台管理服务。"""

from __future__ import annotations

from datetime import datetime, timezone
import time

import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.system.health import get_health_check
from app.modules.system.monitoring import get_system_runtime_snapshot
from app.modules.system.models import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_HIDDEN,
    SYSTEM_SETTING_REGISTER_ENABLED,
    SystemSetting,
)
from app.modules.system.schemas import SystemSettingsRead, SystemSettingsUpdate, SystemStatus

psutil.cpu_percent(interval=None)

_cached_status: SystemStatus | None = None
_cached_at = 0.0
_CACHE_TTL_SECONDS = 2.0
系统设置默认更新时间 = datetime(1970, 1, 1, tzinfo=timezone.utc)
系统设置布尔键 = (
    SYSTEM_SETTING_REGISTER_ENABLED,
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_HIDDEN,
)


async def _set_bool_setting(db: AsyncSession, key: str, value: bool) -> None:
    """写入布尔设置。"""
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=value, str_value=None)
        db.add(setting)
    else:
        setting.bool_value = value
    await db.flush()


async def read_system_settings(db: AsyncSession) -> SystemSettingsRead:
    """读取全部系统设置。"""
    response, _ = await read_system_settings_with_updated_at(db)
    return response


async def read_system_settings_with_updated_at(db: AsyncSession) -> tuple[SystemSettingsRead, datetime]:
    """读取全部系统设置及其最近更新时间。"""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key.in_(系统设置布尔键))
    )
    settings = {setting.key: setting for setting in result.scalars().all()}
    register_enabled_setting = settings.get(SYSTEM_SETTING_REGISTER_ENABLED)
    comments_enabled_setting = settings.get(SYSTEM_SETTING_COMMENTS_ENABLED)
    comments_hidden_setting = settings.get(SYSTEM_SETTING_COMMENTS_HIDDEN)
    response = SystemSettingsRead(
        register_enabled=register_enabled_setting.bool_value
        if register_enabled_setting is not None and register_enabled_setting.bool_value is not None
        else True,
        comments_enabled=comments_enabled_setting.bool_value
        if comments_enabled_setting is not None and comments_enabled_setting.bool_value is not None
        else False,
        comments_hidden=comments_hidden_setting.bool_value
        if comments_hidden_setting is not None and comments_hidden_setting.bool_value is not None
        else True,
    )
    last_modified = max((setting.updated_at for setting in settings.values()), default=系统设置默认更新时间)
    return response, last_modified


async def get_system_status() -> SystemStatus:
    """获取系统状态，并做短时缓存。"""
    global _cached_status, _cached_at
    now = time.monotonic()
    if _cached_status is not None and now - _cached_at < _CACHE_TTL_SECONDS:
        return _cached_status

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    _, health = await get_health_check()
    status = SystemStatus(
        cpu_percent=psutil.cpu_percent(interval=None),
        memory_total_gb=round(mem.total / (1024**3), 2),
        memory_used_gb=round(mem.used / (1024**3), 2),
        memory_percent=mem.percent,
        disk_total_gb=round(disk.total / (1024**3), 2),
        disk_used_gb=round(disk.used / (1024**3), 2),
        disk_percent=disk.percent,
        uptime_seconds=round(time.time() - psutil.boot_time(), 1),
        health=health,
        runtime=await get_system_runtime_snapshot(),
    )
    _cached_status = status
    _cached_at = now
    return status


async def update_system_settings(db: AsyncSession, body: SystemSettingsUpdate) -> SystemSettingsRead:
    """更新系统设置。"""
    if body.register_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_REGISTER_ENABLED, body.register_enabled)
    if body.comments_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, body.comments_enabled)
    if body.comments_hidden is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_HIDDEN, body.comments_hidden)

    return await read_system_settings(db)
