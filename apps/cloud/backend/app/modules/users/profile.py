"""当前用户资料相关服务。"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import 哈希密码, 验证密码
from app.modules.users.cleanup import 删除用户并清理
from app.modules.users.common import (
    应用设置更新,
    确保邮箱可用,
    确保用户名可用,
    规范化昵称输入,
    规范化用户名输入,
)
from app.modules.users.models import 用户, 用户角色
from app.modules.users.schemas import 用户修改密码, 用户更新
from app.modules.auth.sessions import 撤销用户会话


async def 更新当前用户(
    db: AsyncSession,
    user: 用户,
    body: 用户更新,
) -> 用户:
    """更新当前用户资料。"""
    data = body.model_dump(exclude_unset=True)
    if "username" in data and isinstance(data["username"], str):
        data["username"] = 规范化用户名输入(data["username"])
    if "nickname" in data:
        data["nickname"] = 规范化昵称输入(data["nickname"])
    if "username" in data and data["username"] != user.username:
        await 确保用户名可用(db, data["username"], exclude_user_id=user.id)
    if "email" in data:
        await 确保邮箱可用(
            db,
            data["email"],
            current_email_identity=user.email_identity,
            exclude_user_id=user.id,
        )

    settings_data = data.pop("settings", None)
    应用设置更新(user, settings_data)
    for key, value in data.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user, ["settings"])
    return user


async def 修改当前用户密码(
    db: AsyncSession,
    user: 用户,
    body: 用户修改密码,
) -> None:
    """修改当前用户密码。"""
    if not 验证密码(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    user.password_hash = 哈希密码(body.new_password)
    await 撤销用户会话(str(user.id))
    await db.flush()


async def 删除当前用户账号(
    db: AsyncSession,
    user: 用户,
    *,
    password: str,
) -> None:
    """注销当前用户自己的账户。"""
    if user.role == 用户角色.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超级管理员不能注销自己的账户")
    if not 验证密码(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")

    await 撤销用户会话(str(user.id))
    await 删除用户并清理(db, user)
