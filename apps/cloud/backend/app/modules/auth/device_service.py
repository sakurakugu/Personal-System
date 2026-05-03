"""设备认证服务。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import hashlib
import secrets
from types import SimpleNamespace
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import (
    DeviceSessionScope,
    DeviceSessionType,
    UserDeviceSession,
    utcnow,
)
from app.modules.users.models import User, UserRole
from app.shared.kernel.config import settings


DEVICE_TOKEN_HASH_LENGTH = 64


@dataclass(slots=True)
class DeviceLoginResult:
    """设备登录结果。"""

    token: str
    session: UserDeviceSession


def build_device_token() -> str:
    """生成原始设备令牌。"""
    return f"{settings.AUTH_DEVICE_TOKEN_PREFIX}_{secrets.token_urlsafe(32)}"


def build_device_token_hash(token: str) -> str:
    """计算设备令牌哈希。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_device_session_expire_days(
    device_type: DeviceSessionType,
    scope: DeviceSessionScope,
) -> int:
    """计算设备会话有效期天数。"""
    if device_type == DeviceSessionType.widget or scope == DeviceSessionScope.widget_basic:
        return settings.AUTH_DEVICE_WIDGET_EXPIRE_DAYS
    return settings.AUTH_DEVICE_EXPIRE_DAYS


def build_device_session_expiration(
    device_type: DeviceSessionType,
    scope: DeviceSessionScope,
):
    """计算设备会话过期时间。"""
    return utcnow() + timedelta(days=build_device_session_expire_days(device_type, scope))


def validate_device_scope(
    device_type: DeviceSessionType,
    scope: DeviceSessionScope,
) -> None:
    """校验设备类型和权限范围是否匹配。"""
    if scope == DeviceSessionScope.widget_basic and device_type != DeviceSessionType.widget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前设备类型不支持 widget_basic 权限",
        )


def validate_widget_token_issue_source(
    current_session: UserDeviceSession | SimpleNamespace | None,
) -> None:
    """校验当前来源是否允许签发小工具凭证。"""
    if current_session is None:
        return
    session_scope = getattr(current_session, "scope", None)
    if session_scope != DeviceSessionScope.full_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前设备权限不足，不能签发小工具凭证",
        )


def build_device_session_query() -> Select[tuple[UserDeviceSession]]:
    """构造设备会话基础查询。"""
    return select(UserDeviceSession)


async def create_device_session(
    db: AsyncSession,
    *,
    user_id: UUID,
    device_name: str,
    device_type: DeviceSessionType,
    scope: DeviceSessionScope,
    client_version: str | None = None,
    platform: str | None = None,
    last_ip: str | None = None,
    last_user_agent: str | None = None,
) -> DeviceLoginResult:
    """创建设备会话并返回原始令牌。"""
    validate_device_scope(device_type, scope)

    token = build_device_token()
    session = UserDeviceSession(
        user_id=user_id,
        token_hash=build_device_token_hash(token),
        device_name=device_name,
        device_type=device_type,
        scope=scope,
        client_version=client_version,
        platform=platform,
        last_ip=last_ip,
        last_user_agent=last_user_agent,
        expires_at=build_device_session_expiration(device_type, scope),
        last_used_at=utcnow(),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return DeviceLoginResult(token=token, session=session)


async def get_device_session_by_token(
    db: AsyncSession,
    token: str,
) -> UserDeviceSession:
    """按原始令牌查找有效设备会话。"""
    token_hash = build_device_token_hash(token)
    result = await db.execute(
        build_device_session_query().where(UserDeviceSession.token_hash == token_hash)
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


async def get_device_session_user(
    db: AsyncSession,
    session: UserDeviceSession,
) -> User:
    """根据设备会话读取当前用户。"""
    result = await db.execute(
        select(User).where(User.id == session.user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


async def list_user_device_sessions(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> list[UserDeviceSession]:
    """列出用户设备会话。"""
    result = await db.execute(
        build_device_session_query()
        .where(UserDeviceSession.user_id == user_id)
        .order_by(UserDeviceSession.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_device_session(
    session: UserDeviceSession,
) -> None:
    """吊销设备会话。"""
    if session.revoked_at is None:
        session.revoked_at = utcnow()


async def revoke_device_session_by_id(
    db: AsyncSession,
    *,
    target_session_id: UUID,
    current_user: User,
) -> None:
    """按 ID 吊销设备会话。"""
    result = await db.execute(
        build_device_session_query().where(UserDeviceSession.id == target_session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备会话不存在")
    if session.user_id != current_user.id and current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该设备会话")
    await revoke_device_session(session)


async def revoke_all_user_device_sessions(
    db: AsyncSession,
    *,
    current_user: User,
    exclude_session_id: UUID | None = None,
) -> int:
    """吊销当前用户的全部设备会话。"""
    result = await db.execute(
        build_device_session_query().where(UserDeviceSession.user_id == current_user.id)
    )
    sessions = list(result.scalars().all())
    revoked_count = 0
    for session in sessions:
        if session.revoked_at is not None:
            continue
        if exclude_session_id is not None and session.id == exclude_session_id:
            continue
        await revoke_device_session(session)
        revoked_count += 1
    return revoked_count
