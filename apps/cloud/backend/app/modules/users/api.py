"""用户资料路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.admin import (
    管理员创建用户,
    管理员删除用户,
    管理员列出用户,
    管理员重置用户密码,
    管理员更新用户,
)
from app.modules.users.models import 用户
from app.modules.users.permissions import (
    确保删除目标允许,
    确保密码重置目标允许,
    确保更新目标允许,
    获取可管理角色,
    解析可管理角色,
)
from app.modules.users.profile import (
    修改当前用户密码,
    删除当前用户账号,
    更新当前用户,
)
from app.modules.users.schemas import (
    管理员更新用户,
    用户修改密码,
    管理员创建用户,
    用户密码重置,
    用户信息,
    用户更新,
)
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.auth.deps import 获取当前用户, 要求管理员权限
from app.shared.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=用户信息)
async def get_me(user: 用户 = Depends(获取当前用户)):
    """获取当前登录用户的资料。"""
    return user


@router.patch("/me", response_model=用户信息)
async def update_me(
    body: 用户更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户的资料。"""
    return await 更新当前用户(db, user, body)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def 修改我的密码(
    body: 用户修改密码,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户的密码。"""
    await 修改当前用户密码(db, user, body)


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    keyword: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    admin: 用户 = Depends(要求管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表。"""
    return await 管理员列出用户(
        db,
        admin,
        page=page,
        page_size=page_size,
        keyword=keyword,
        role=role,
        is_active=is_active,
    )


@router.post("", response_model=用户信息, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: 管理员创建用户,
    admin: 用户 = Depends(要求管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """创建用户。"""
    return await 管理员创建用户(db, admin, body)


@router.patch("/{user_id}", response_model=用户信息)
async def update_user(
    user_id: UUID,
    body: 管理员更新用户,
    admin: 用户 = Depends(要求管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息。"""
    return await 管理员更新用户(db, admin, user_id=user_id, body=body)


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def 重置用户密码(
    user_id: UUID,
    body: 用户密码重置,
    admin: 用户 = Depends(要求管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """重置用户密码。"""
    await 管理员重置用户密码(db, admin, user_id=user_id, body=body)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: 用户 = Depends(要求管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """删除用户。"""
    await 管理员删除用户(db, admin, user_id=user_id)


@router.delete("/me/account", status_code=status.HTTP_204_NO_CONTENT)
async def 删除我的账号(
    password: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """注销当前用户自己的账户。"""
    await 删除当前用户账号(db, user, password=password)


__all__ = [
    "router",
    "确保删除目标允许",
    "确保密码重置目标允许",
    "确保更新目标允许",
    "获取可管理角色",
    "解析可管理角色",
]
