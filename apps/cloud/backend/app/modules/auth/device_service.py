"""设备认证服务。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import hashlib
import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import (
    设备会话范围,
    设备会话类型,
    用户设备会话,
    utcnow,
)
from app.modules.users.models import 用户, 用户角色
from app.shared.kernel.config import settings


DEVICE_TOKEN_HASH_LENGTH = 64


@dataclass(slots=True)
class 设备登录结果:
    """设备登录结果。"""

    token: str
    session: 用户设备会话


def 构建设备令牌() -> str:
    """生成原始设备令牌。"""
    return f"{settings.AUTH_DEVICE_TOKEN_PREFIX}_{secrets.token_urlsafe(32)}"


def 构建设备令牌哈希(token: str) -> str:
    """计算设备令牌哈希。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def 构建设备会话过期天数(
    device_type: 设备会话类型,
    scope: 设备会话范围,
) -> int:
    """计算设备会话有效期天数。"""
    return settings.AUTH_DEVICE_EXPIRE_DAYS


def 构建设备会话过期时间(
    device_type: 设备会话类型,
    scope: 设备会话范围,
):
    """计算设备会话过期时间。"""
    return utcnow() + timedelta(days=构建设备会话过期天数(device_type, scope))


def 校验设备权限范围(
    device_type: 设备会话类型,
    scope: 设备会话范围,
) -> None:
    """校验设备类型和权限范围是否匹配。"""
    if scope != 设备会话范围.full_client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的设备权限范围")


def 构建设备会话查询() -> Select[tuple[用户设备会话]]:
    """构造设备会话基础查询。"""
    return select(用户设备会话)


async def 创建设备会话(
    db: AsyncSession,
    *,
    user_id: UUID,
    device_name: str,
    device_type: 设备会话类型,
    scope: 设备会话范围,
    client_version: str | None = None,
    platform: str | None = None,
    last_ip: str | None = None,
    last_user_agent: str | None = None,
) -> 设备登录结果:
    """创建设备会话并返回原始令牌。"""
    校验设备权限范围(device_type, scope)

    token = 构建设备令牌()
    session = 用户设备会话(
        user_id=user_id,
        token_hash=构建设备令牌哈希(token),
        device_name=device_name,
        device_type=device_type,
        scope=scope,
        client_version=client_version,
        platform=platform,
        last_ip=last_ip,
        last_user_agent=last_user_agent,
        expires_at=构建设备会话过期时间(device_type, scope),
        last_used_at=utcnow(),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return 设备登录结果(token=token, session=session)


async def 按令牌获取设备会话(
    db: AsyncSession,
    token: str,
) -> 用户设备会话:
    """按原始令牌查找有效设备会话。"""
    token_hash = 构建设备令牌哈希(token)
    result = await db.execute(
        构建设备会话查询().where(用户设备会话.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="设备登录已失效")
    if session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="设备登录已失效")
    if session.expires_at <= utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="设备登录已过期")

    session.last_used_at = utcnow()
    return session


async def 获取设备会话用户(
    db: AsyncSession,
    session: 用户设备会话,
) -> 用户:
    """根据设备会话读取当前用户。"""
    result = await db.execute(
        select(用户).where(用户.id == session.user_id, 用户.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


async def 列出用户设备会话(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> list[用户设备会话]:
    """列出用户设备会话。"""
    result = await db.execute(
        构建设备会话查询()
        .where(用户设备会话.user_id == user_id)
        .order_by(用户设备会话.created_at.desc())
    )
    return list(result.scalars().all())


async def 吊销设备会话(
    session: 用户设备会话,
) -> None:
    """吊销设备会话。"""
    if session.revoked_at is None:
        session.revoked_at = utcnow()


async def 按ID吊销设备会话(
    db: AsyncSession,
    *,
    target_session_id: UUID,
    current_user: 用户,
) -> None:
    """按 ID 吊销设备会话。"""
    result = await db.execute(
        构建设备会话查询().where(用户设备会话.id == target_session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备会话不存在")
    if session.user_id != current_user.id and current_user.role != 用户角色.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该设备会话")
    await 吊销设备会话(session)


async def 吊销全部用户设备会话(
    db: AsyncSession,
    *,
    current_user: 用户,
    exclude_session_id: UUID | None = None,
) -> int:
    """吊销当前用户的全部设备会话。"""
    result = await db.execute(
        构建设备会话查询().where(用户设备会话.user_id == current_user.id)
    )
    sessions = list(result.scalars().all())
    revoked_count = 0
    for session in sessions:
        if session.revoked_at is not None:
            continue
        if exclude_session_id is not None and session.id == exclude_session_id:
            continue
        await 吊销设备会话(session)
        revoked_count += 1
    return revoked_count
