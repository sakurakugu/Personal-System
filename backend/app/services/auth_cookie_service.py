"""认证 Cookie 辅助服务。"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import Request, Response
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.schemas.auth import TokenResponse

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


def write_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    """写入访问令牌和刷新令牌 Cookie。"""
    domain = _normalize_cookie_domain()
    samesite = _normalize_cookie_samesite()
    response.set_cookie(
        key=settings.AUTH_ACCESS_COOKIE_NAME,
        value=tokens.access_token,
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=domain,
    )
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=tokens.refresh_token,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 86400,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=samesite,
        domain=domain,
    )


def clear_auth_cookies(response: Response) -> None:
    """清理认证 Cookie。"""
    domain = _normalize_cookie_domain()
    response.delete_cookie(
        key=settings.AUTH_ACCESS_COOKIE_NAME,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
        domain=domain,
    )
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        domain=domain,
    )


def get_access_token_from_request(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = None,
) -> str | None:
    """优先从 Bearer 头，其次从访问令牌 Cookie 读取 access token。"""
    if creds is not None and creds.scheme.lower() == "bearer" and creds.credentials:
        return creds.credentials
    return request.cookies.get(settings.AUTH_ACCESS_COOKIE_NAME)


def get_refresh_token_from_request(request: Request) -> str | None:
    """从刷新令牌 Cookie 读取 refresh token。"""
    return request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
