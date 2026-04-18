"""当前用户资料相关服务。"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserChangePassword, UserUpdate
from app.services.session_service import revoke_user_sessions
from app.services.user_service import delete_user_with_cleanup
from app.services.users.common import (
    apply_settings_update,
    ensure_email_available,
    ensure_username_available,
    normalize_nickname_input,
    normalize_username_input,
)


async def update_current_user(
    db: AsyncSession,
    user: User,
    body: UserUpdate,
) -> User:
    """更新当前用户资料。"""
    data = body.model_dump(exclude_unset=True)
    if "username" in data and isinstance(data["username"], str):
        data["username"] = normalize_username_input(data["username"])
    if "nickname" in data:
        data["nickname"] = normalize_nickname_input(data["nickname"])
    if "username" in data and data["username"] != user.username:
        await ensure_username_available(db, data["username"], exclude_user_id=user.id)
    if "email" in data:
        await ensure_email_available(
            db,
            data["email"],
            current_email_identity=user.email_identity,
            exclude_user_id=user.id,
        )

    settings_data = data.pop("settings", None)
    apply_settings_update(user, settings_data)
    for key, value in data.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user, ["settings"])
    return user


async def change_current_user_password(
    db: AsyncSession,
    user: User,
    body: UserChangePassword,
) -> None:
    """修改当前用户密码。"""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    user.password_hash = hash_password(body.new_password)
    await revoke_user_sessions(str(user.id))
    await db.flush()


async def delete_current_user_account(
    db: AsyncSession,
    user: User,
    *,
    password: str,
) -> None:
    """注销当前用户自己的账户。"""
    if user.role == UserRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超级管理员不能注销自己的账户")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")

    await revoke_user_sessions(str(user.id))
    await delete_user_with_cleanup(db, user)
