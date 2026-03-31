"""管理系统状态路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_super_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.system import SystemSettingsRead, SystemSettingsUpdate, SystemStatus
from app.services.admin_service import get_system_status, read_system_settings, update_system_settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system", response_model=SystemStatus)
async def system_status(_super_admin: User = Depends(require_super_admin)):
    """
    获取系统状态信息。

    Args:
        _admin: 当前管理员

    Returns:
        SystemStatus: 系统状态数据
    """
    return await get_system_status()


@router.get("/public-settings", response_model=SystemSettingsRead)
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """
    获取公开系统设置。

    Args:
        db: 数据库会话

    Returns:
        SystemSettingsRead: 系统设置
    """
    return await read_system_settings(db)


@router.get("/settings", response_model=SystemSettingsRead)
async def get_settings(
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取完整系统设置。

    Args:
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        SystemSettingsRead: 系统设置
    """
    return await read_system_settings(db)


@router.patch("/settings", response_model=SystemSettingsRead)
async def patch_settings(
    body: SystemSettingsUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新系统设置。

    Args:
        body: 设置更新请求
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        SystemSettingsRead: 更新后的系统设置
    """
    return await update_system_settings(db, body)
