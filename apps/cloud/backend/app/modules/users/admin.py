"""管理员用户管理服务。"""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import 哈希密码
from app.modules.users.cleanup import 删除用户并清理
from app.modules.users.common import (
    应用设置更新,
    确保邮箱可用,
    确保用户名可用,
    确保用户名或邮箱可用于创建,
    获取用户或404,
    规范化昵称输入,
    规范化用户名输入,
)
from app.modules.users.models import User, 构建默认用户设置
from app.modules.users.permissions import (
    确保删除目标允许,
    确保密码重置目标允许,
    确保更新目标允许,
    获取可管理角色,
    解析可管理角色,
)
from app.modules.users.schemas import UserAdminUpdate, UserCreateByAdmin, UserPasswordReset, UserRead
from app.shared.kernel.pagination import PaginatedResponse
from app.modules.auth.sessions import 撤销用户会话


async def 管理员列出用户(
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
    query = select(User).where(User.role.in_(获取可管理角色(admin)))
    if keyword:
        kw = f"%{keyword.strip()}%"
        query = query.where(or_(User.username.ilike(kw), User.nickname.ilike(kw), User.email.ilike(kw)))
    if role:
        query = query.where(User.role == 解析可管理角色(admin, role, "管理员不能查看超级管理员"))
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


async def 管理员创建用户(
    db: AsyncSession,
    admin: User,
    body: UserCreateByAdmin,
) -> User:
    """创建用户。"""
    await 确保用户名或邮箱可用于创建(db, username=body.username, email=body.email)
    user = User(
        username=body.username,
        nickname=(body.nickname.strip() if body.nickname and body.nickname.strip() else body.username),
        email=body.email,
        password_hash=哈希密码(body.password),
        role=解析可管理角色(admin, body.role, "管理员不能设置超级管理员角色"),
        bio=body.bio,
        avatar_url=body.avatar_url,
        is_active=body.is_active,
        settings=构建默认用户设置(),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["settings"])
    return user


async def 管理员更新用户(
    db: AsyncSession,
    admin: User,
    *,
    user_id: UUID,
    body: UserAdminUpdate,
) -> User:
    """更新用户信息。"""
    target = await 获取用户或404(db, user_id)
    确保更新目标允许(admin, target)

    data = body.model_dump(exclude_unset=True)
    if "username" in data and isinstance(data["username"], str):
        data["username"] = 规范化用户名输入(data["username"])
    if "nickname" in data:
        data["nickname"] = 规范化昵称输入(data["nickname"])
    if target.id == admin.id and ("role" in data or "is_active" in data):
        raise HTTPException(status_code=400, detail="不能修改自己的角色或状态")

    if "username" in data and data["username"] != target.username:
        await 确保用户名可用(db, data["username"], exclude_user_id=target.id)
    if "email" in data:
        await 确保邮箱可用(
            db,
            data["email"],
            current_email_identity=target.email_identity,
            exclude_user_id=target.id,
        )

    if "role" in data:
        target.role = 解析可管理角色(admin, data.pop("role"), "管理员不能设置超级管理员角色")
    should_revoke_sessions = "is_active" in data and data["is_active"] is False
    settings_data = data.pop("settings", None)
    应用设置更新(target, settings_data)
    for key, value in data.items():
        setattr(target, key, value)
    if should_revoke_sessions:
        await 撤销用户会话(str(target.id))
    await db.flush()
    await db.refresh(target, ["settings"])
    return target


async def 管理员重置用户密码(
    db: AsyncSession,
    admin: User,
    *,
    user_id: UUID,
    body: UserPasswordReset,
) -> None:
    """重置用户密码。"""
    target = await 获取用户或404(db, user_id)
    确保密码重置目标允许(admin, target)
    target.password_hash = 哈希密码(body.password)
    await 撤销用户会话(str(target.id))
    await db.flush()


async def 管理员删除用户(
    db: AsyncSession,
    admin: User,
    *,
    user_id: UUID,
) -> None:
    """删除用户。"""
    target = await 获取用户或404(db, user_id)
    确保删除目标允许(admin, target)
    await 撤销用户会话(str(target.id))
    await 删除用户并清理(db, target)
