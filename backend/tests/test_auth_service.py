"""认证服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from app.services.auth_service import build_blacklist_ttl_seconds, build_user_nickname


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


if __name__ == "__main__":
    unittest.main()
