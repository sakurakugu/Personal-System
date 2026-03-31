"""认证服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from app.services.auth_service import (
    build_dev_account_config,
    build_blacklist_ttl_seconds,
    build_user_nickname,
    is_dev_login_enabled,
)


class AuthServiceTest(unittest.TestCase):
    """认证服务纯逻辑测试。"""

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


if __name__ == "__main__":
    unittest.main()
