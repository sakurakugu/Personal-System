"""首页 Feed 服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.modules.feed.service import (
    _构建Feed首页缓存键,
    _获取Feed首页缓存版本,
    _规范化Feed缓存版本,
    清除Feed首页缓存,
)


class FeedServiceTest(unittest.IsolatedAsyncioTestCase):
    """Feed 服务纯逻辑测试。"""

    def test_缓存版本为空时会回退到零(self) -> None:
        self.assertEqual(_规范化Feed缓存版本(None), "0")
        self.assertEqual(_规范化Feed缓存版本(""), "0")
        self.assertEqual(_规范化Feed缓存版本("3"), "3")

    def test_缓存键会包含版本和用户信息(self) -> None:
        cache_key = _构建Feed首页缓存键(
            2,
            20,
            None,
            version="5",
            visitor_id="visitor-1",
        )

        self.assertEqual(cache_key, "feed:home:v=5:page=2:size=20:user=guest:visitor=visitor-1")

    async def test_读取缓存版本时缺省为零(self) -> None:
        redis = AsyncMock()
        redis.get.return_value = None

        with patch("app.modules.feed.service.get_redis", AsyncMock(return_value=redis)):
            version = await _获取Feed首页缓存版本()

        self.assertEqual(version, "0")

    async def test_失效缓存时只递增版本号(self) -> None:
        redis = AsyncMock()

        with patch("app.modules.feed.service.get_redis", AsyncMock(return_value=redis)):
            await 清除Feed首页缓存()

        redis.incr.assert_awaited_once_with("feed:home:version")


if __name__ == "__main__":
    unittest.main()
