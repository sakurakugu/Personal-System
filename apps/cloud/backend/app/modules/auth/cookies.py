"""认证 Cookie 辅助能力。"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import Request, Response

from app.modules.auth.sessions import 会话数据
from app.shared.kernel.config import settings

CookieSameSite = Literal["lax", "strict", "none"]


def _规范化Cookie域() -> str | None:
    """将空域名配置归一化为 None。"""
    domain = settings.AUTH_COOKIE_DOMAIN.strip()
    return domain or None


def _规范化Cookie同站策略() -> CookieSameSite:
    """将 SameSite 配置归一化为合法值。"""
    value = settings.AUTH_COOKIE_SAMESITE.strip().lower()
    if value in {"lax", "strict", "none"}:
        return cast(CookieSameSite, value)
    return "lax"


def 写入认证Cookie(response: Response, session: 会话数据) -> None:
    """写入 Session Cookie 和 CSRF Cookie。"""
    domain = _规范化Cookie域()
    samesite = _规范化Cookie同站策略()
    response.set_cookie(
        key=settings.AUTH_SESSION_COOKIE_NAME,
        value=session.session_id,
        max_age=settings.AUTH_SESSION_EXPIRE_DAYS * 86400,
        path=settings.AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=domain,
    )
    response.set_cookie(
        key=settings.AUTH_CSRF_COOKIE_NAME,
        value=session.csrf_token,
        max_age=settings.AUTH_SESSION_EXPIRE_DAYS * 86400,
        path=settings.AUTH_COOKIE_PATH,
        httponly=False,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=domain,
    )


def 清除认证Cookie(response: Response) -> None:
    """清理认证 Cookie。"""
    domain = _规范化Cookie域()
    response.delete_cookie(
        key=settings.AUTH_SESSION_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=domain,
    )
    response.delete_cookie(
        key=settings.AUTH_CSRF_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=domain,
    )


def 从请求获取会话ID(request: Request) -> str | None:
    """从请求中读取 Session ID。"""
    return request.cookies.get(settings.AUTH_SESSION_COOKIE_NAME)
