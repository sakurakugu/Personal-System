"""认证 Cookie 辅助服务。"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import Request, Response

from app.core.config import settings
from app.services.session_service import SessionData

CookieSameSite = Literal["lax", "strict", "none"]


def _normalize_cookie_domain() -> str | None:
    """将空域名配置归一化为 None。"""
    domain = settings.AUTH_COOKIE_DOMAIN.strip()
    return domain or None


def _normalize_cookie_samesite() -> CookieSameSite:
    """将 SameSite 配置归一化为合法值。"""
    value = settings.AUTH_COOKIE_SAMESITE.strip().lower()
    if value in {"lax", "strict", "none"}:
        return cast(CookieSameSite, value)
    return "lax"


def write_auth_cookies(response: Response, session: SessionData) -> None:
    """写入 Session Cookie 和 CSRF Cookie。"""
    domain = _normalize_cookie_domain()
    samesite = _normalize_cookie_samesite()
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


def clear_auth_cookies(response: Response) -> None:
    """清理认证 Cookie。"""
    domain = _normalize_cookie_domain()
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
    # keys = (
    #     settings.AUTH_SESSION_COOKIE_NAME,
    #     settings.AUTH_CSRF_COOKIE_NAME,
    # )

    # for key in keys:
    #     response.delete_cookie(
    #         key=key,
    #         path=settings.AUTH_COOKIE_PATH,
    #         domain=domain,
    #     )
    #     # 兼容清理历史上未设置 Domain 的 host-only Cookie。
    #     response.delete_cookie(
    #         key=key,
    #         path=settings.AUTH_COOKIE_PATH,
    #     )


def get_session_id_from_request(request: Request) -> str | None:
    """从请求中读取 Session ID。"""
    return request.cookies.get(settings.AUTH_SESSION_COOKIE_NAME)
