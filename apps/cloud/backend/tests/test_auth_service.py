"""认证服务测试。"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.modules.auth.cookies import (
    清除认证Cookie,
    从请求获取会话ID,
    写入认证Cookie,
)
from app.modules.auth.service import (
    _确保注册已启用,
    构建开发账号配置,
    构建用户昵称,
    是否启用开发登录,
)
from app.modules.auth.sessions import 会话数据, 构建会话TTL秒数


class 认证服务测试(unittest.TestCase):
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
        self.assertEqual(构建用户昵称("alice", None), "alice")
        self.assertEqual(构建用户昵称("alice", "   "), "alice")
        self.assertEqual(构建用户昵称("alice", " 小爱 "), "小爱")

    def test_session_ttl_会按天转换为秒(self) -> None:
        self.assertEqual(构建会话TTL秒数(), 30 * 86400)

    def test_开发环境判定(self) -> None:
        from app.modules.auth import service as auth_service

        original_debug = auth_service.settings.APP_DEBUG
        original_env = auth_service.settings.APP_ENV
        try:
            auth_service.settings.APP_DEBUG = False
            auth_service.settings.APP_ENV = "production"
            self.assertFalse(是否启用开发登录())

            auth_service.settings.APP_ENV = "development"
            self.assertTrue(是否启用开发登录())

            auth_service.settings.APP_ENV = "production"
            auth_service.settings.APP_DEBUG = True
            self.assertTrue(是否启用开发登录())
        finally:
            auth_service.settings.APP_DEBUG = original_debug
            auth_service.settings.APP_ENV = original_env

    def test_开发账号配置映射(self) -> None:
        from app.modules.auth import service as auth_service

        admin = 构建开发账号配置("admin")
        user = 构建开发账号配置("user")

        self.assertEqual(admin[0], auth_service.settings.DEV_ADMIN_USERNAME)
        self.assertEqual(admin[3].value, "admin")
        self.assertEqual(user[0], auth_service.settings.DEV_USER_USERNAME)
        self.assertEqual(user[3].value, "user")

    def test_认证_cookie_可写入与清理(self) -> None:
        response = Response()
        写入认证Cookie(
            response,
            会话数据(session_id="session-demo", user_id="user-demo", csrf_token="csrf-demo"),
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
        清除认证Cookie(cleared_response)
        cleared_headers = [
            value.decode("utf-8")
            for name, value in cleared_response.raw_headers
            if name == b"set-cookie"
        ]
        self.assertTrue(any("session_id=" in header and "Max-Age=0" in header for header in cleared_headers))
        self.assertTrue(any("csrf_token=" in header and "Max-Age=0" in header for header in cleared_headers))

    def test_session_id_可从_cookie_读取(self) -> None:
        request = self._build_request(cookies={"session_id": "session-cookie"})
        self.assertEqual(从请求获取会话ID(request), "session-cookie")


class 认证服务异步测试(unittest.IsolatedAsyncioTestCase):
    """认证服务异步逻辑测试。"""

    async def test_未配置注册开关时默认关闭注册(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with self.assertRaises(HTTPException) as context:
            await _确保注册已启用(db)

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "注册已关闭")

    async def test_明确开启注册时允许通过(self) -> None:
        db = AsyncMock()
        db.get.return_value = SimpleNamespace(bool_value=True)

        await _确保注册已启用(db)


if __name__ == "__main__":
    unittest.main()
