"""后台管理服务。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import time

import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.system.health import 获取健康检查
from app.modules.system.monitoring import 获取系统运行时快照
from app.modules.system.models import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_HIDDEN,
    SYSTEM_SETTING_REGISTER_ENABLED,
    SystemSetting,
)
from app.modules.system.schemas import SystemSettingsRead, SystemSettingsUpdate, SystemStatus

psutil.cpu_percent(interval=None)

logger = logging.getLogger(__name__)
_cached_status: SystemStatus | None = None
_cached_at = 0.0
_cache_lock = asyncio.Lock()
_sampling_task: asyncio.Task[None] | None = None
_STATUS_SAMPLING_INTERVAL_SECONDS = 15.0
_STATUS_STALE_SECONDS = 45.0
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


async def 读取系统设置(db: AsyncSession) -> SystemSettingsRead:
    """读取全部系统设置。"""
    response, _ = await 读取系统设置含更新时间(db)
    return response


async def 读取系统设置含更新时间(db: AsyncSession) -> tuple[SystemSettingsRead, datetime]:
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
        else False,
        comments_enabled=comments_enabled_setting.bool_value
        if comments_enabled_setting is not None and comments_enabled_setting.bool_value is not None
        else False,
        comments_hidden=comments_hidden_setting.bool_value
        if comments_hidden_setting is not None and comments_hidden_setting.bool_value is not None
        else True,
    )
    last_modified = max((setting.updated_at for setting in settings.values()), default=系统设置默认更新时间)
    return response, last_modified


async def _构建系统状态() -> SystemStatus:
    """实时采样一次系统状态。"""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    _, health = await 获取健康检查()
    return SystemStatus(
        cpu_percent=psutil.cpu_percent(interval=None),
        memory_total_gb=round(mem.total / (1024**3), 2),
        memory_used_gb=round(mem.used / (1024**3), 2),
        memory_percent=mem.percent,
        disk_total_gb=round(disk.total / (1024**3), 2),
        disk_used_gb=round(disk.used / (1024**3), 2),
        disk_percent=disk.percent,
        uptime_seconds=round(time.time() - psutil.boot_time(), 1),
        health=health,
        runtime=await 获取系统运行时快照(),
    )


def _is_status_stale(now: float) -> bool:
    """判断当前缓存是否已经过期。"""
    return _cached_status is None or now - _cached_at >= _STATUS_STALE_SECONDS


async def 刷新系统状态缓存(*, force: bool = False) -> SystemStatus:
    """刷新系统状态缓存。"""
    global _cached_status, _cached_at
    now = time.monotonic()
    if not force and not _is_status_stale(now) and _cached_status is not None:
        return _cached_status

    async with _cache_lock:
        now = time.monotonic()
        if not force and not _is_status_stale(now) and _cached_status is not None:
            return _cached_status

        status = await _构建系统状态()
        _cached_status = status
        _cached_at = now
        return status


async def _系统状态采样循环() -> None:
    """后台循环采样系统状态。"""
    try:
        while True:
            try:
                await 刷新系统状态缓存(force=True)
            except Exception:
                logger.exception("后台采样系统状态失败")
            await asyncio.sleep(_STATUS_SAMPLING_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        raise


async def 启动系统状态采样() -> None:
    """启动系统状态后台采样。"""
    global _sampling_task
    if _sampling_task is not None and not _sampling_task.done():
        return

    await 刷新系统状态缓存(force=True)
    _sampling_task = asyncio.create_task(_系统状态采样循环())


async def 停止系统状态采样() -> None:
    """停止系统状态后台采样。"""
    global _sampling_task
    if _sampling_task is None:
        return

    task = _sampling_task
    _sampling_task = None
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def get_system_status() -> SystemStatus:
    """获取系统状态快照。"""
    now = time.monotonic()
    if _cached_status is not None and not _is_status_stale(now):
        return _cached_status
    return await 刷新系统状态缓存(force=True)


async def 更新系统设置(db: AsyncSession, body: SystemSettingsUpdate) -> SystemSettingsRead:
    """更新系统设置。"""
    if body.register_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_REGISTER_ENABLED, body.register_enabled)
    if body.comments_enabled is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_ENABLED, body.comments_enabled)
    if body.comments_hidden is not None:
        await _set_bool_setting(db, SYSTEM_SETTING_COMMENTS_HIDDEN, body.comments_hidden)

    return await 读取系统设置(db)
