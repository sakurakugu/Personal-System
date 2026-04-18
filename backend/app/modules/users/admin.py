"""管理员用户管理服务。"""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.cleanup import delete_user_with_cleanup
from app.modules.users.common import (
    apply_settings_update,
    ensure_email_available,
    ensure_username_available,
    ensure_username_or_email_available_for_create,
    get_user_or_404,
    normalize_nickname_input,
    normalize_username_input,
)
from app.modules.users.models import User, build_default_user_settings
from app.modules.users.permissions import (
    ensure_delete_target_allowed,
    ensure_password_reset_target_allowed,
    ensure_update_target_allowed,
    get_manageable_roles,
    parse_manageable_role,
)
from app.modules.users.schemas import UserAdminUpdate, UserCreateByAdmin, UserPasswordReset, UserRead
from app.schemas.shared import PaginatedResponse
from app.services.session_service import revoke_user_sessions


async def list_users_by_admin(
    db: AsyncSession,
    admin: User,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
    role: str | None,
    is_active: bool | None,
) -> PaginatedResponse:
    """获取用户列表。"""
    query = select(User).where(User.role.in_(get_manageable_roles(admin)))
    if keyword:
        kw = f"%{keyword.strip()}%"
        query = query.where(or_(User.username.ilike(kw), User.nickname.ilike(kw), User.email.ilike(kw)))
    if role:
        query = query.where(User.role == parse_manageable_role(admin, role, "管理员不能查看超级管理员"))
    if is_active is not None:
        query = query.where(User.is_active.is_(is_active))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    items = (
        await db.execute(
            query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()
    return PaginatedResponse(
        items=[UserRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def create_user_by_admin(
    db: AsyncSession,
    admin: User,
    body: UserCreateByAdmin,
) -> User:
    """创建用户。"""
    await ensure_username_or_email_available_for_create(db, username=body.username, email=body.email)
    user = User(
        username=body.username,
        nickname=(body.nickname.strip() if body.nickname and body.nickname.strip() else body.username),
        email=body.email,
        password_hash=hash_password(body.password),
        role=parse_manageable_role(admin, body.role, "管理员不能设置超级管理员角色"),
        bio=body.bio,
        avatar_url=body.avatar_url,
        is_active=body.is_active,
        settings=build_default_user_settings(),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["settings"])
    return user


async def update_user_by_admin(
    db: AsyncSession,
    admin: User,
    *,
    user_id: UUID,
    body: UserAdminUpdate,
) -> User:
    """更新用户信息。"""
    target = await get_user_or_404(db, user_id)
    ensure_update_target_allowed(admin, target)

    data = body.model_dump(exclude_unset=True)
    if "username" in data and isinstance(data["username"], str):
        data["username"] = normalize_username_input(data["username"])
    if "nickname" in data:
        data["nickname"] = normalize_nickname_input(data["nickname"])
    if target.id == admin.id and ("role" in data or "is_active" in data):
        raise HTTPException(status_code=400, detail="不能修改自己的角色或状态")

    if "username" in data and data["username"] != target.username:
        await ensure_username_available(db, data["username"], exclude_user_id=target.id)
    if "email" in data:
        await ensure_email_available(
            db,
            data["email"],
            current_email_identity=target.email_identity,
            exclude_user_id=target.id,
        )

    if "role" in data:
        target.role = parse_manageable_role(admin, data.pop("role"), "管理员不能设置超级管理员角色")
    should_revoke_sessions = "is_active" in data and data["is_active"] is False
    settings_data = data.pop("settings", None)
    apply_settings_update(target, settings_data)
    for key, value in data.items():
        setattr(target, key, value)
    if should_revoke_sessions:
        await revoke_user_sessions(str(target.id))
    await db.flush()
    await db.refresh(target, ["settings"])
    return target


async def reset_user_password_by_admin(
    db: AsyncSession,
    admin: User,
    *,
    user_id: UUID,
    body: UserPasswordReset,
) -> None:
    """重置用户密码。"""
    target = await get_user_or_404(db, user_id)
    ensure_password_reset_target_allowed(admin, target)
    target.password_hash = hash_password(body.password)
    await revoke_user_sessions(str(target.id))
    await db.flush()


async def delete_user_by_admin(
    db: AsyncSession,
    admin: User,
    *,
    user_id: UUID,
) -> None:
    """删除用户。"""
    target = await get_user_or_404(db, user_id)
    ensure_delete_target_allowed(admin, target)
    await revoke_user_sessions(str(target.id))
    await delete_user_with_cleanup(db, target)
