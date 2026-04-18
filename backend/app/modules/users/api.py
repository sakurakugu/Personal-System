"""用户资料路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.admin import (
    create_user_by_admin,
    delete_user_by_admin,
    list_users_by_admin,
    reset_user_password_by_admin,
    update_user_by_admin,
)
from app.modules.users.models import User
from app.modules.users.permissions import (
    ensure_delete_target_allowed,
    ensure_password_reset_target_allowed,
    ensure_update_target_allowed,
    get_manageable_roles,
    parse_manageable_role,
)
from app.modules.users.profile import (
    change_current_user_password,
    delete_current_user_account,
    update_current_user,
)
from app.modules.users.schemas import (
    UserAdminUpdate,
    UserChangePassword,
    UserCreateByAdmin,
    UserPasswordReset,
    UserRead,
    UserUpdate,
)
from app.schemas.shared import PaginatedResponse
from app.shared.auth.deps import get_current_user, require_admin
from app.shared.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前登录用户的资料。"""
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户的资料。"""
    return await update_current_user(db, user, body)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    body: UserChangePassword,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户的密码。"""
    await change_current_user_password(db, user, body)


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    keyword: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表。"""
    return await list_users_by_admin(
        db,
        admin,
        page=page,
        page_size=page_size,
        keyword=keyword,
        role=role,
        is_active=is_active,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateByAdmin,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建用户。"""
    return await create_user_by_admin(db, admin, body)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    body: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息。"""
    return await update_user_by_admin(db, admin, user_id=user_id, body=body)


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(
    user_id: UUID,
    body: UserPasswordReset,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """重置用户密码。"""
    await reset_user_password_by_admin(db, admin, user_id=user_id, body=body)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除用户。"""
    await delete_user_by_admin(db, admin, user_id=user_id)


@router.delete("/me/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    password: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """注销当前用户自己的账户。"""
    await delete_current_user_account(db, user, password=password)


__all__ = [
    "router",
    "ensure_delete_target_allowed",
    "ensure_password_reset_target_allowed",
    "ensure_update_target_allowed",
    "get_manageable_roles",
    "parse_manageable_role",
]
