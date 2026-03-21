"""管理系统状态路由（psutil）。

此模块提供系统监控和管理接口，包括：
- 系统状态监控（CPU、内存、磁盘使用率）
- 系统设置管理（评论开关、注册开关等）

所有接口都需要管理员权限。
"""

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

# 创建路由器，前缀为 /admin，标签为 admin
router = APIRouter(prefix="/admin", tags=["admin"])

# 初始化 CPU 百分比计算（第一次调用返回 0，需要预热）
psutil.cpu_percent(interval=None)

# 系统状态缓存
_cached_status: SystemStatus | None = None
_cached_at = 0.0
_CACHE_TTL_SECONDS = 2.0  # 缓存有效期 2 秒


async def _get_bool_setting(db: AsyncSession, key: str, default: bool) -> bool:
    """
    从数据库获取布尔类型的系统设置。

    Args:
        db: 数据库会话
        key: 设置项的键名
        default: 默认值（设置不存在时返回）

    Returns:
        bool: 设置值
    """
    setting = await db.get(SystemSetting, key)
    if setting is None or setting.bool_value is None:
        return default
    return setting.bool_value


async def _get_str_setting(db: AsyncSession, key: str, default: str) -> str:
    """
    从数据库获取字符串类型的系统设置。

    Args:
        db: 数据库会话
        key: 设置项的键名
        default: 默认值（设置不存在时返回）

    Returns:
        str: 设置值
    """
    setting = await db.get(SystemSetting, key)
    if setting is None or setting.str_value is None:
        return default
    return setting.str_value


async def _set_bool_setting(db: AsyncSession, key: str, value: bool) -> None:
    """
    设置布尔类型的系统设置。

    如果设置不存在则创建，存在则更新。

    Args:
        db: 数据库会话
        key: 设置项的键名
        value: 设置值
    """
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=value, str_value=None)
        db.add(setting)
    else:
        setting.bool_value = value
    await db.flush()


async def _set_str_setting(db: AsyncSession, key: str, value: str) -> None:
    """
    设置字符串类型的系统设置。

    如果设置不存在则创建，存在则更新。

    Args:
        db: 数据库会话
        key: 设置项的键名
        value: 设置值
    """
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=None, str_value=value)
        db.add(setting)
    else:
        setting.str_value = value
    await db.flush()


async def _read_system_settings(db: AsyncSession) -> SystemSettingsRead:
    """
    读取所有系统设置。

    Args:
        db: 数据库会话

    Returns:
        SystemSettingsRead: 系统设置数据
    """
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
    """
    获取系统状态信息。

    包括 CPU 使用率、内存使用情况、磁盘使用情况和系统运行时间。
    结果缓存 2 秒以减少 psutil 调用频率。

    Args:
        _admin: 当前管理员用户（依赖注入）

    Returns:
        SystemStatus: 系统状态数据
    """
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
    """
    获取公开的系统设置。

    无需认证，用于前端展示系统配置（如评论是否开启等）。

    Args:
        db: 数据库会话

    Returns:
        SystemSettingsRead: 系统设置数据
    """
    return await _read_system_settings(db)


@router.get("/settings", response_model=SystemSettingsRead)
async def get_settings(
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取系统设置（超级管理员）。

    Args:
        _super_admin: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        SystemSettingsRead: 系统设置数据
    """
    return await _read_system_settings(db)


@router.patch("/settings", response_model=SystemSettingsRead)
async def update_settings(
    body: SystemSettingsUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新系统设置（超级管理员）。

    可设置的选项：
    - comments_enabled: 是否开启评论功能
    - comments_stealth: 是否开启隐身模式（评论仅自己和管理员可见）
    - comments_min_role: 查看评论的最低角色要求
    - register_enabled: 是否开放用户注册

    Args:
        body: 更新的设置数据
        _super_admin: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        SystemSettingsRead: 更新后的系统设置数据

    Raises:
        HTTPException: 400 - 角色值无效
    """
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
