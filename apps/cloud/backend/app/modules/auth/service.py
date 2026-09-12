"""认证服务。"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import 哈希密码, 验证密码
from app.modules.users.models import 用户, 用户角色, 构建默认用户设置
from app.modules.auth.schemas import 登录请求
from app.shared.kernel.config import settings


def 构建用户昵称(username: str, nickname: str | None) -> str:
    """生成用户昵称。"""
    if nickname is None:
        return username
    normalized = nickname.strip()
    return normalized or username


def 是否启用开发登录() -> bool:
    """判断是否启用开发环境一键登录。"""
    return settings.APP_DEBUG or settings.APP_ENV == "development"


def 构建开发账号配置(_legacy_role: str | None = None) -> tuple[str, str, str, 用户角色]:
    """返回单用户模式的开发账号配置。"""
    return (
        settings.ADMIN_USERNAME,
        settings.ADMIN_EMAIL,
        settings.ADMIN_PASSWORD,
        用户角色.user,
    )


async def _按用户名获取用户(db: AsyncSession, username: str) -> 用户 | None:
    """按用户名查询用户。"""
    result = await db.execute(select(用户).where(用户.username == username))
    return result.scalar_one_or_none()


async def login_user(db: AsyncSession, body: 登录请求) -> 用户:
    """用户登录。"""
    user = await _按用户名获取用户(db, body.username)
    if user is None or not 验证密码(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


async def 确保开发登录用户(db: AsyncSession, _legacy_role: str | None = None) -> 用户:
    """读取单用户模式的 owner，供开发环境快捷登录。"""
    if not 是否启用开发登录():
        raise HTTPException(status_code=404, detail="接口不存在")

    user = (await db.execute(select(用户).order_by(用户.created_at.asc(), 用户.id.asc()).limit(1))).scalar_one_or_none()
    if user is None:
        username, email, password, user_role = 构建开发账号配置()
        user = 用户(
            username=username,
            nickname=username,
            email=email,
            password_hash=哈希密码(password),
            role=user_role,
            is_active=True,
            settings=构建默认用户设置(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user, ["settings"])
    return user


async def 开发用户登录(db: AsyncSession, _legacy_role: str | None = None) -> 用户:
    """开发模式下一键登录唯一拥有者。"""
    return await 确保开发登录用户(db)
