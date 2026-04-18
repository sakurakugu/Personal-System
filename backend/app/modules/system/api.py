"""管理系统状态路由。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import build_conditional_json_response
from app.modules.users.models import User
from app.modules.system.schemas import SystemSettingsRead, SystemSettingsUpdate, SystemStatus
from app.modules.system.service import get_system_status, read_system_settings, read_system_settings_with_updated_at, update_system_settings
from app.shared.auth.deps import require_super_admin
from app.shared.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system", response_model=SystemStatus)
async def system_status(_super_admin: User = Depends(require_super_admin)):
    """获取系统状态信息。"""
    return await get_system_status()


@router.get("/public-settings", response_model=SystemSettingsRead)
async def get_public_settings(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取公开系统设置。"""
    payload, last_modified = await read_system_settings_with_updated_at(db)
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("/settings", response_model=SystemSettingsRead)
async def get_settings(
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取完整系统设置。"""
    return await read_system_settings(db)


@router.patch("/settings", response_model=SystemSettingsRead)
async def patch_settings(
    body: SystemSettingsUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新系统设置。"""
    return await update_system_settings(db, body)
