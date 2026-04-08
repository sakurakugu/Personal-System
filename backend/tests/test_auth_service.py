"""认证服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request
from starlette.responses import Response

from app.schemas.auth import TokenResponse
from app.services.auth_cookie_service import (
    clear_auth_cookies,
    get_access_token_from_request,
    get_refresh_token_from_request,
    write_auth_cookies,
)
from app.services.auth_service import (
    build_dev_account_config,
    build_blacklist_ttl_seconds,
    build_user_nickname,
    is_dev_login_enabled,
)


class AuthServiceTest(unittest.TestCase):
    """认证服务纯逻辑测试。"""

    @staticmethod
    def _build_request(
        *,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
    ) -> Request:
        raw_headers: list[tuple[bytes, bytes]] = []
        for key, value in (headers or {}).items():
            raw_headers.append((key.lower().encode("utf-8"), value.encode("utf-8")))
        if cookies:
            cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
            raw_headers.append((b"cookie", cookie_header.encode("utf-8")))
        return Request({"type": "http", "headers": raw_headers})

    def test_空昵称会回退到用户名(self) -> None:
        self.assertEqual(build_user_nickname("alice", None), "alice")
        self.assertEqual(build_user_nickname("alice", "   "), "alice")
        self.assertEqual(build_user_nickname("alice", " 小爱 "), "小爱")

    def test_黑名单_ttl_会基于过期时间并且至少为一秒(self) -> None:
        fallback = 3600
        future_expire_at = datetime.now(timezone.utc) + timedelta(seconds=120)
        past_expire_at = datetime.now(timezone.utc) - timedelta(seconds=30)

        self.assertGreaterEqual(build_blacklist_ttl_seconds(future_expire_at, fallback), 100)
        self.assertEqual(build_blacklist_ttl_seconds(past_expire_at, fallback), 1)
        self.assertEqual(build_blacklist_ttl_seconds(None, fallback), fallback)

    def test_开发环境判定(self) -> None:
        from app.services import auth_service

        original_debug = auth_service.settings.APP_DEBUG
        original_env = auth_service.settings.APP_ENV
        try:
            auth_service.settings.APP_DEBUG = False
            auth_service.settings.APP_ENV = "production"
            self.assertFalse(is_dev_login_enabled())

            auth_service.settings.APP_ENV = "development"
            self.assertTrue(is_dev_login_enabled())

            auth_service.settings.APP_ENV = "production"
            auth_service.settings.APP_DEBUG = True
            self.assertTrue(is_dev_login_enabled())
        finally:
            auth_service.settings.APP_DEBUG = original_debug
            auth_service.settings.APP_ENV = original_env

    def test_开发账号配置映射(self) -> None:
        from app.services import auth_service

        super_admin = build_dev_account_config("super_admin")
        admin = build_dev_account_config("admin")
        user = build_dev_account_config("user")

        self.assertEqual(super_admin[0], auth_service.settings.SUPER_ADMIN_USERNAME)
        self.assertEqual(super_admin[3].value, "super_admin")
        self.assertEqual(admin[0], auth_service.settings.DEV_ADMIN_USERNAME)
        self.assertEqual(admin[3].value, "admin")
        self.assertEqual(user[0], auth_service.settings.DEV_USER_USERNAME)
        self.assertEqual(user[3].value, "user")

    def test_认证_cookie_可写入与清理(self) -> None:
        response = Response()
        write_auth_cookies(
            response,
            TokenResponse(access_token="access-demo", refresh_token="refresh-demo"),
        )

        cookie_headers = [
            value.decode("utf-8")
            for name, value in response.raw_headers
            if name == b"set-cookie"
        ]
        self.assertTrue(any("access_token=access-demo" in header for header in cookie_headers))
        self.assertTrue(any("refresh_token=refresh-demo" in header for header in cookie_headers))
        self.assertTrue(any("HttpOnly" in header for header in cookie_headers))

        cleared_response = Response()
        clear_auth_cookies(cleared_response)
        cleared_headers = [
            value.decode("utf-8")
            for name, value in cleared_response.raw_headers
            if name == b"set-cookie"
        ]
        self.assertTrue(any("access_token=" in header and "Max-Age=0" in header for header in cleared_headers))
        self.assertTrue(any("refresh_token=" in header and "Max-Age=0" in header for header in cleared_headers))

    def test_访问令牌优先取_bearer_否则回退_cookie(self) -> None:
        cookie_request = self._build_request(cookies={"access_token": "cookie-access"})
        self.assertEqual(get_access_token_from_request(cookie_request), "cookie-access")

        bearer_request = self._build_request(cookies={"access_token": "cookie-access"})
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="header-access")
        self.assertEqual(get_access_token_from_request(bearer_request, creds), "header-access")

    def test_刷新令牌可从_cookie_读取(self) -> None:
        request = self._build_request(cookies={"refresh_token": "refresh-cookie"})
        self.assertEqual(get_refresh_token_from_request(request), "refresh-cookie")


if __name__ == "__main__":
    unittest.main()
