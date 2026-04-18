"""首页 Feed 服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.feed_service import (
    _build_feed_home_cache_key,
    _get_feed_home_cache_version,
    _normalize_feed_cache_version,
    invalidate_feed_home_cache,
)


class FeedServiceTest(unittest.IsolatedAsyncioTestCase):
    """Feed 服务纯逻辑测试。"""

    def test_缓存版本为空时会回退到零(self) -> None:
        self.assertEqual(_normalize_feed_cache_version(None), "0")
        self.assertEqual(_normalize_feed_cache_version(""), "0")
        self.assertEqual(_normalize_feed_cache_version("3"), "3")

    def test_缓存键会包含版本和用户信息(self) -> None:
        cache_key = _build_feed_home_cache_key(
            2,
            20,
            None,
            version="5",
        )

        self.assertEqual(cache_key, "feed:home:v=5:page=2:size=20:user=guest")

    async def test_读取缓存版本时缺省为零(self) -> None:
        redis = AsyncMock()
        redis.get.return_value = None

        with patch("app.services.feed_service.get_redis", AsyncMock(return_value=redis)):
            version = await _get_feed_home_cache_version()

        self.assertEqual(version, "0")

    async def test_失效缓存时只递增版本号(self) -> None:
        redis = AsyncMock()

        with patch("app.services.feed_service.get_redis", AsyncMock(return_value=redis)):
            await invalidate_feed_home_cache()

        redis.incr.assert_awaited_once_with("feed:home:version")


if __name__ == "__main__":
    unittest.main()
