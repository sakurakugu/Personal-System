"""用户资料路由。

此模块提供用户管理接口，包括：
- 当前用户资料管理（查看、修改、修改密码）
- 用户管理（管理员）：列表查询、创建、修改、删除、重置密码

用户角色：user < admin < super_admin
"""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import (
    UserAdminUpdate,
    UserChangePassword,
    UserCreateByAdmin,
    UserPasswordReset,
    UserRead,
    UserUpdate,
)
from app.schemas.shared import PaginatedResponse
from app.services.user_service import delete_user_with_cleanup

# 创建路由器，前缀为 /users，标签为 users
router = APIRouter(prefix="/users", tags=["users"])


def _normalize_username(value: str) -> str:
    """
    规范化用户名输入。

    Args:
        value: 原始用户名

    Returns:
        str: 去首尾空白后的用户名

    Raises:
        HTTPException: 400 - 用户名不能为空
    """
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    return normalized


def _parse_user_role(role_value: str) -> UserRole:
    """
    解析用户角色字符串为 UserRole 枚举。

    Args:
        role_value: 角色值字符串

    Returns:
        UserRole: 角色枚举值

    Raises:
        HTTPException: 400 - 无效的角色
    """
    try:
        return UserRole(role_value)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的角色")


def _get_manageable_roles(admin: User) -> tuple[UserRole, ...]:
    """
    返回当前管理员可管理的角色范围。

    Args:
        admin: 当前管理员用户

    Returns:
        tuple[UserRole, ...]: 可管理的角色集合
    """
    if admin.role == UserRole.super_admin:
        return (UserRole.user, UserRole.admin, UserRole.super_admin)
    return (UserRole.user, UserRole.admin)


def _parse_manageable_role(admin: User, role_value: str, detail: str) -> UserRole:
    """
    解析并校验管理员可操作的角色。

    Args:
        admin: 当前管理员用户
        role_value: 角色值字符串
        detail: 越权时返回的错误信息

    Returns:
        UserRole: 通过校验的角色

    Raises:
        HTTPException: 403 - 当前管理员无权操作该角色
    """
    role = _parse_user_role(role_value)
    if role not in _get_manageable_roles(admin):
        raise HTTPException(status_code=403, detail=detail)
    return role


def _ensure_update_target_allowed(admin: User, target: User) -> None:
    """
    校验当前管理员是否可以修改目标用户资料。

    Args:
        admin: 当前管理员用户
        target: 目标用户

    Raises:
        HTTPException: 403 - 无权修改目标用户
    """
    if admin.role == UserRole.admin and target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能修改超级管理员")
    if target.role == UserRole.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="不能修改其他超级管理员")


def _ensure_password_reset_target_allowed(admin: User, target: User) -> None:
    """
    校验当前管理员是否可以重置目标用户密码。

    Args:
        admin: 当前管理员用户
        target: 目标用户

    Raises:
        HTTPException: 403 - 无权重置目标用户密码
    """
    if admin.role == UserRole.admin and target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能重置超级管理员密码")
    if target.role == UserRole.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="不能修改其他超级管理员")


def _ensure_delete_target_allowed(admin: User, target: User) -> None:
    """
    校验当前管理员是否可以删除目标用户。

    Args:
        admin: 当前管理员用户
        target: 目标用户

    Raises:
        HTTPException: 400 - 不能删除自己
        HTTPException: 403 - 无权删除目标用户
    """
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    if admin.role == UserRole.admin and target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能删除超级管理员")
    if target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="不能删除超级管理员")


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
    data = body.model_dump(exclude_unset=True)
    if "username" in data and isinstance(data["username"], str):
        data["username"] = _normalize_username(data["username"])
    if "nickname" in data and isinstance(data["nickname"], str):
        data["nickname"] = data["nickname"].strip() or None
    if "username" in data and data["username"] != user.username:
        exists = await db.execute(select(User).where(User.username == data["username"], User.id != user.id))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="用户名已被使用")
    if "email" in data and data["email"] != user.email:
        exists = await db.execute(select(User).where(User.email == data["email"], User.id != user.id))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="邮箱已被使用")
    for k, v in data.items():
        setattr(user, k, v)
    await db.flush()
    await db.refresh(user)
    return user


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
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    user.password_hash = hash_password(body.new_password)
    await db.flush()
    return


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
    q = select(User).where(User.role.in_(_get_manageable_roles(admin)))
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(or_(User.username.ilike(kw), User.nickname.ilike(kw), User.email.ilike(kw)))
    if role:
        q = q.where(User.role == _parse_manageable_role(admin, role, "管理员不能查看超级管理员"))
    if is_active is not None:
        q = q.where(User.is_active.is_(is_active))
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    return PaginatedResponse(
        items=[UserRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
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
    exists = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名或邮箱已被使用")
    user = User(
        username=body.username,
        nickname=(body.nickname.strip() if body.nickname and body.nickname.strip() else body.username),
        email=body.email,
        password_hash=hash_password(body.password),
        role=_parse_manageable_role(admin, body.role, "管理员不能设置超级管理员角色"),
        bio=body.bio,
        avatar_url=body.avatar_url,
        is_active=body.is_active,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


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
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    _ensure_update_target_allowed(admin, target)

    data = body.model_dump(exclude_unset=True)
    if "username" in data and isinstance(data["username"], str):
        data["username"] = _normalize_username(data["username"])
    if "nickname" in data and isinstance(data["nickname"], str):
        data["nickname"] = data["nickname"].strip() or None
    if target.id == admin.id and ("role" in data or "is_active" in data):
        raise HTTPException(status_code=400, detail="不能修改自己的角色或状态")

    if "username" in data and data["username"] != target.username:
        exists = await db.execute(
            select(User).where(User.username == data["username"], User.id != target.id)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="用户名已被使用")
    if "email" in data and data["email"] != target.email:
        exists = await db.execute(select(User).where(User.email == data["email"], User.id != target.id))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="邮箱已被使用")

    if "role" in data:
        target.role = _parse_manageable_role(admin, data.pop("role"), "管理员不能设置超级管理员角色")
    for k, v in data.items():
        setattr(target, k, v)
    await db.flush()
    await db.refresh(target)
    return target


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
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    _ensure_password_reset_target_allowed(admin, target)
    target.password_hash = hash_password(body.password)
    await db.flush()
    return


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
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    _ensure_delete_target_allowed(admin, target)
    await delete_user_with_cleanup(db, target)
    return


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
    # 超级管理员不能注销自己的账户
    if user.role == UserRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超级管理员不能注销自己的账户")

    # 验证密码
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")

    await delete_user_with_cleanup(db, user)
    return
