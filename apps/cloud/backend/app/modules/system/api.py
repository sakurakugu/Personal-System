"""管理系统状态路由。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import 构建条件JSON响应
from app.modules.users.models import User
from app.modules.system.schemas import (
    SystemSettingsRead,
    SystemSettingsUpdate,
    SystemStatus,
    TwikooPasswordResetRequest,
    TwikooPasswordStateRead,
)
from app.modules.system.service import get_system_status, 读取系统设置, 读取系统设置_with_updated_at, 更新系统设置
from app.modules.system.twikoo_password_service import (
    TwikooPasswordManageError,
    获取Twikoo密码状态,
    重置Twikoo管理员密码,
)
from app.shared.auth.deps import 要求超级管理员权限
from app.shared.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/system", response_model=SystemStatus)
async def system_status(_super_admin: User = Depends(要求超级管理员权限)):
    """获取系统状态信息。"""
    return await get_system_status()


@router.get("/public-settings", response_model=SystemSettingsRead)
async def 获取公开设置(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取公开系统设置。"""
    payload, last_modified = await 读取系统设置_with_updated_at(db)
    return 构建条件JSON响应(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("/settings", response_model=SystemSettingsRead)
async def get_settings(
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取完整系统设置。"""
    return await 读取系统设置(db)


@router.patch("/settings", response_model=SystemSettingsRead)
async def patch_settings(
    body: SystemSettingsUpdate,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """更新系统设置。"""
    return await 更新系统设置(db, body)


@router.get("/twikoo/password", response_model=TwikooPasswordStateRead)
async def 获取Twikoo密码(
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取 Twikoo 密码运维状态与最近一次备忘。"""
    return await 获取Twikoo密码状态(db)


@router.post("/twikoo/password/reset", response_model=TwikooPasswordStateRead)
async def 重置Twikoo密码接口(
    body: TwikooPasswordResetRequest,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """重置 Twikoo 管理密码。"""
    try:
        return await 重置Twikoo管理员密码(db, body.password)
    except TwikooPasswordManageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
