"""匿名访客互动辅助能力。"""

from __future__ import annotations

import inspect
from typing import Awaitable, Literal, TypeVar, cast

from fastapi import Request, Response

from app.core.redis import get_redis
from app.shared.kernel.config import settings
from app.utils.uuid import generate_uuid7

_VISITOR_COOKIE_NAME = "visitor_id"
_VISITOR_COOKIE_MAX_AGE = 86400 * 365 * 5

T = TypeVar("T")


async def _resolve_redis_result(value: Awaitable[T] | T) -> T:
    """兼容 Redis 类型声明里的同步/异步联合返回值。"""
    if inspect.isawaitable(value):
        return await value
    return value


def _normalize_cookie_domain() -> str | None:
    """将空域名配置归一化为 None。"""
    domain = settings.AUTH_COOKIE_DOMAIN.strip()
    return domain or None


CookieSameSite = Literal["lax", "strict", "none"]


def _normalize_cookie_samesite() -> CookieSameSite:
    """将 SameSite 配置归一化为合法值。"""
    value = settings.AUTH_COOKIE_SAMESITE.strip().lower()
    if value in {"lax", "strict", "none"}:
        return cast(CookieSameSite, value)
    return "lax"


def ensure_visitor_id(request: Request, response: Response) -> str:
    """确保请求具备匿名访客标识。"""
    visitor_id = request.cookies.get(_VISITOR_COOKIE_NAME)
    if visitor_id:
        return visitor_id

    visitor_id = str(generate_uuid7())
    response.set_cookie(
        key=_VISITOR_COOKIE_NAME,
        value=visitor_id,
        max_age=_VISITOR_COOKIE_MAX_AGE,
        path=settings.AUTH_COOKIE_PATH,
        httponly=False,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=_normalize_cookie_samesite(),
        domain=_normalize_cookie_domain(),
    )
    return visitor_id


def get_visitor_id(request: Request) -> str | None:
    """从请求中读取匿名访客标识。"""
    return request.cookies.get(_VISITOR_COOKIE_NAME)


async def add_set_member_once(key: str, member: str) -> bool:
    """向 Redis 集合写入成员，仅在首次写入时返回真。"""
    redis = await get_redis()
    added = await _resolve_redis_result(redis.sadd(key, member))
    return bool(added)


async def remove_set_member(key: str, member: str) -> bool:
    """从 Redis 集合移除成员，仅在确实移除时返回真。"""
    redis = await get_redis()
    removed = await _resolve_redis_result(redis.srem(key, member))
    return bool(removed)


async def has_set_member(key: str, member: str) -> bool:
    """判断 Redis 集合是否包含指定成员。"""
    redis = await get_redis()
    exists = await _resolve_redis_result(redis.sismember(key, member))
    return bool(exists)


async def mark_key_once(key: str, *, expire_seconds: int | None = None) -> bool:
    """按键记录一次性操作，仅在首次写入时返回真。"""
    redis = await get_redis()
    created = await _resolve_redis_result(redis.set(key, "1", nx=True, ex=expire_seconds))
    return bool(created)
