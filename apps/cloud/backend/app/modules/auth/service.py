"""认证服务。"""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import 哈希密码, 验证密码
from app.modules.system.models import SYSTEM_SETTING_REGISTER_ENABLED, 系统设置
from app.modules.users.models import 用户, 用户角色, 构建默认用户设置
from app.modules.auth.schemas import 登录请求, 注册请求
from app.shared.kernel.config import settings
from app.utils.email import 构建邮箱身份

DevLoginRole = Literal["super_admin", "admin", "user"]


def 构建用户昵称(username: str, nickname: str | None) -> str:
    """生成用户昵称。"""
    if nickname is None:
        return username
    normalized = nickname.strip()
    return normalized or username


def 是否启用开发登录() -> bool:
    """判断是否启用开发环境一键登录。"""
    return settings.APP_DEBUG or settings.APP_ENV == "development"


def 构建开发账号配置(role: DevLoginRole) -> tuple[str, str, str, 用户角色]:
    """根据角色返回开发账号配置。"""
    if role == "super_admin":
        return (
            settings.SUPER_ADMIN_USERNAME,
            settings.SUPER_ADMIN_EMAIL,
            settings.SUPER_ADMIN_PASSWORD,
            用户角色.super_admin,
        )
    if role == "admin":
        return (
            settings.DEV_ADMIN_USERNAME,
            settings.DEV_ADMIN_EMAIL,
            settings.DEV_ADMIN_PASSWORD,
            用户角色.admin,
        )
    return (
        settings.DEV_USER_USERNAME,
        settings.DEV_USER_EMAIL,
        settings.DEV_USER_PASSWORD,
        用户角色.user,
    )


async def _确保注册已启用(db: AsyncSession) -> None:
    """校验当前是否允许注册。"""
    setting = await db.get(系统设置, SYSTEM_SETTING_REGISTER_ENABLED)
    if setting is None or setting.bool_value is not True:
        raise HTTPException(status_code=403, detail="注册已关闭")


async def _确保身份唯一(db: AsyncSession, username: str, email: str) -> None:
    """校验用户名和邮箱未被占用。"""
    email_identity = 构建邮箱身份(email)
    exists = await db.execute(
        select(用户).where((用户.username == username) | (用户.email_identity == email_identity))
    )
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被使用")


async def _按用户名获取用户(db: AsyncSession, username: str) -> 用户 | None:
    """按用户名查询用户。"""
    result = await db.execute(select(用户).where(用户.username == username))
    return result.scalar_one_or_none()


async def _按邮箱获取用户(db: AsyncSession, email: str) -> 用户 | None:
    """按邮箱判重键查询用户。"""
    result = await db.execute(select(用户).where(用户.email_identity == 构建邮箱身份(email)))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, body: 注册请求) -> 用户:
    """注册用户。"""
    await _确保注册已启用(db)
    await _确保身份唯一(db, body.username, str(body.email))
    user = 用户(
        username=body.username,
        nickname=构建用户昵称(body.username, body.nickname),
        email=body.email,
        password_hash=哈希密码(body.password),
        settings=构建默认用户设置(),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["settings"])
    return user


async def login_user(db: AsyncSession, body: 登录请求) -> 用户:
    """用户登录。"""
    user = await _按用户名获取用户(db, body.username)
    if user is None or not 验证密码(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


async def 确保开发登录用户(db: AsyncSession, role: DevLoginRole) -> 用户:
    """确保开发模式快捷登录账号存在且可用。"""
    if not 是否启用开发登录():
        raise HTTPException(status_code=404, detail="接口不存在")

    username, email, password, user_role = 构建开发账号配置(role)
    user = await _按用户名获取用户(db, username)
    if user is None:
        user = await _按邮箱获取用户(db, email)

    password_hash = 哈希密码(password)
    nickname = username
    if user is None:
        user = 用户(
            username=username,
            nickname=nickname,
            email=email,
            password_hash=password_hash,
            role=user_role,
            is_active=True,
            settings=构建默认用户设置(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user, ["settings"])
        return user

    user.username = username
    user.nickname = nickname
    user.email = email
    user.password_hash = password_hash
    user.role = user_role
    user.is_active = True
    user.ensure_settings()
    await db.commit()
    await db.refresh(user, ["settings"])
    return user


async def 开发用户登录(db: AsyncSession, role: DevLoginRole) -> 用户:
    """开发模式下按角色一键登录。"""
    return await 确保开发登录用户(db, role)
