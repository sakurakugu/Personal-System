"""服务端 Session 管理。"""

from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass
import json
import secrets
from typing import TypeVar, cast

from app.core.redis import get_redis
from app.shared.kernel.config import settings

T = TypeVar("T")


@dataclass(slots=True)
class SessionData:
    """已解析的会话数据。"""

    session_id: str
    user_id: str
    csrf_token: str


def build_session_ttl_seconds() -> int:
    """返回 Session 的统一有效期。"""
    return settings.AUTH_SESSION_EXPIRE_DAYS * 86400


def build_session_key(session_id: str) -> str:
    """构造 Session 存储键。"""
    return f"session:{session_id}"


def build_user_sessions_key(user_id: str) -> str:
    """构造用户会话索引键。"""
    return f"user_sessions:{user_id}"


def _serialize_session_payload(user_id: str, csrf_token: str) -> str:
    """序列化会话载荷。"""
    return json.dumps({"user_id": user_id, "csrf_token": csrf_token}, ensure_ascii=True)


def _deserialize_session_payload(session_id: str, payload: str) -> SessionData | None:
    """反序列化会话载荷。"""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None

    user_id = data.get("user_id")
    csrf_token = data.get("csrf_token")
    if not isinstance(user_id, str) or not user_id:
        return None
    if not isinstance(csrf_token, str) or not csrf_token:
        return None
    return SessionData(session_id=session_id, user_id=user_id, csrf_token=csrf_token)


async def _resolve_redis_result(value: Awaitable[T] | T) -> T:
    """兼容 redis 类型声明里的同步/异步联合返回值。"""
    if isinstance(value, Awaitable):
        return await cast(Awaitable[T], value)
    return value


async def create_user_session(user_id: str) -> SessionData:
    """为指定用户创建新的服务端 Session。"""
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    ttl = build_session_ttl_seconds()
    redis = await get_redis()

    await redis.setex(
        build_session_key(session_id),
        ttl,
        _serialize_session_payload(user_id, csrf_token),
    )
    await _resolve_redis_result(redis.sadd(build_user_sessions_key(user_id), session_id))
    await _resolve_redis_result(redis.expire(build_user_sessions_key(user_id), ttl))
    return SessionData(session_id=session_id, user_id=user_id, csrf_token=csrf_token)


async def get_session(session_id: str | None) -> SessionData | None:
    """按 Session ID 读取会话。"""
    if not session_id:
        return None

    redis = await get_redis()
    payload = await redis.get(build_session_key(session_id))
    if not isinstance(payload, str) or not payload:
        return None

    session = _deserialize_session_payload(session_id, payload)
    if session is None:
        await redis.delete(build_session_key(session_id))
        return None
    return session


async def delete_session(session_id: str | None) -> None:
    """删除指定 Session。"""
    if not session_id:
        return

    redis = await get_redis()
    payload = await redis.get(build_session_key(session_id))
    session = _deserialize_session_payload(session_id, payload) if isinstance(payload, str) else None
    await redis.delete(build_session_key(session_id))
    if session is not None:
        await _resolve_redis_result(redis.srem(build_user_sessions_key(session.user_id), session_id))


async def revoke_user_sessions(user_id: str) -> None:
    """撤销指定用户的全部 Session。"""
    redis = await get_redis()
    sessions_key = build_user_sessions_key(user_id)
    session_ids = list(await _resolve_redis_result(redis.smembers(sessions_key)))
    if session_ids:
        await redis.delete(*(build_session_key(session_id) for session_id in session_ids))
    await redis.delete(sessions_key)
