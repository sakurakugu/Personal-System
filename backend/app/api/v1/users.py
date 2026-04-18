"""用户资料路由。

此模块提供用户管理接口，包括：
- 当前用户资料管理（查看、修改、修改密码）
- 用户管理（管理员）：列表查询、创建、修改、删除、重置密码

用户角色：user < admin < super_admin
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.shared import PaginatedResponse
from app.schemas.user import (
    UserAdminUpdate,
    UserChangePassword,
    UserCreateByAdmin,
    UserPasswordReset,
    UserRead,
    UserUpdate,
)
from app.services.users.admin import (
    create_user_by_admin,
    delete_user_by_admin,
    list_users_by_admin,
    reset_user_password_by_admin,
    update_user_by_admin,
)
from app.services.users.profile import (
    change_current_user_password,
    delete_current_user_account,
    update_current_user,
)

# 创建路由器，前缀为 /users，标签为 users
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    """
    获取当前登录用户的资料。

    Args:
        user: 当前登录用户（依赖注入）

    Returns:
        UserRead: 用户信息
    """
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新当前用户的资料。

    可以修改：昵称、用户名、邮箱、头像、个人简介等。
    用户名和邮箱修改时会检查是否已被其他用户使用。

    Args:
        body: 用户更新数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        UserRead: 更新后的用户信息

    Raises:
        HTTPException: 409 - 用户名或邮箱已被使用
    """
    return await update_current_user(db, user, body)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    body: UserChangePassword,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    修改当前用户的密码。

    Args:
        body: 密码修改数据（当前密码、新密码）
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 400 - 当前密码错误
        HTTPException: 400 - 新密码不能与旧密码相同
    """
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
    """
    获取用户列表（管理员）。

    支持按关键词（用户名/昵称/邮箱）、角色、状态筛选，支持分页。
    普通管理员只能查看普通用户和管理员，超级管理员可查看全部角色。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量，范围 1-50
        keyword: 搜索关键词，匹配用户名、昵称、邮箱
        role: 角色筛选
        is_active: 是否激活筛选
        admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的用户列表
    """
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
    """
    创建用户（管理员）。

    管理员可以直接创建用户并设置角色。
    普通管理员不能创建超级管理员。

    Args:
        body: 用户创建数据
        admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        UserRead: 创建的用户

    Raises:
        HTTPException: 409 - 用户名或邮箱已被使用
    """
    return await create_user_by_admin(db, admin, body)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    body: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户信息（管理员）。

    普通管理员不能修改超级管理员的信息，也不能将任何用户设置为超级管理员。
    所有管理员都不能修改自己的角色或状态，超级管理员仍不能修改其他超级管理员的信息。

    Args:
        user_id: 用户 ID
        body: 用户更新数据
        admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        UserRead: 更新后的用户

    Raises:
        HTTPException: 404 - 用户不存在
        HTTPException: 403 - 无权修改超级管理员
        HTTPException: 400 - 不能修改自己的角色或状态
        HTTPException: 409 - 用户名或邮箱已被使用
    """
    return await update_user_by_admin(db, admin, user_id=user_id, body=body)


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(
    user_id: UUID,
    body: UserPasswordReset,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    重置用户密码（管理员）。

    普通管理员不能重置超级管理员密码。
    超级管理员仍不能重置其他超级管理员的密码。

    Args:
        user_id: 用户 ID
        body: 密码重置数据（新密码）
        admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 用户不存在
        HTTPException: 403 - 无权重置超级管理员密码
    """
    await reset_user_password_by_admin(db, admin, user_id=user_id, body=body)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    删除用户（管理员）。

    不能删除自己，不能删除超级管理员。

    Args:
        user_id: 用户 ID
        admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 用户不存在
        HTTPException: 400 - 不能删除自己
        HTTPException: 403 - 不能删除超级管理员
    """
    await delete_user_by_admin(db, admin, user_id=user_id)


@router.delete("/me/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    password: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    注销当前用户自己的账户。

    只允许自己注销自己的账户，且只有管理员及以下权限可以注销（超级管理员不能注销自己）。
    需要验证当前密码。

    Args:
        password: 当前密码验证
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 403 - 超级管理员不能注销自己的账户
        HTTPException: 400 - 密码错误
    """
    await delete_current_user_account(db, user, password=password)
