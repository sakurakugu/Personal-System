"""认证服务测试。"""

from __future__ import annotations

import unittest

from starlette.requests import Request
from starlette.responses import Response

from app.services.auth_cookie_service import (
    clear_auth_cookies,
    get_session_id_from_request,
    write_auth_cookies,
)
from app.services.auth_service import (
    build_dev_account_config,
    build_user_nickname,
    is_dev_login_enabled,
)
from app.services.session_service import SessionData, build_session_ttl_seconds


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

    def test_session_ttl_会按天转换为秒(self) -> None:
        self.assertEqual(build_session_ttl_seconds(), 30 * 86400)

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
            SessionData(session_id="session-demo", user_id="user-demo", csrf_token="csrf-demo"),
        )

        cookie_headers = [
            value.decode("utf-8")
            for name, value in response.raw_headers
            if name == b"set-cookie"
        ]
        self.assertTrue(any("session_id=session-demo" in header for header in cookie_headers))
        self.assertTrue(any("csrf_token=csrf-demo" in header for header in cookie_headers))
        self.assertTrue(any("session_id=session-demo" in header and "HttpOnly" in header for header in cookie_headers))

        cleared_response = Response()
        clear_auth_cookies(cleared_response)
        cleared_headers = [
            value.decode("utf-8")
            for name, value in cleared_response.raw_headers
            if name == b"set-cookie"
        ]
        self.assertTrue(any("session_id=" in header and "Max-Age=0" in header for header in cleared_headers))
        self.assertTrue(any("csrf_token=" in header and "Max-Age=0" in header for header in cleared_headers))

    def test_session_id_可从_cookie_读取(self) -> None:
        request = self._build_request(cookies={"session_id": "session-cookie"})
        self.assertEqual(get_session_id_from_request(request), "session-cookie")


if __name__ == "__main__":
    unittest.main()
