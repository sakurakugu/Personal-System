"""动态服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.modules.moments.models import Moment
from app.modules.moments.service import like_moment, record_moment_view, unlike_moment
from app.utils.uuid import generate_uuid7


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_moment() -> Moment:
    """构造测试动态。"""
    return Moment(
        id=generate_uuid7(),
        title="测试动态",
        content="hello",
        is_published=True,
        view_count=0,
        like_count=0,
        user_id=generate_uuid7(),
        published_at=utc_dt(2026, 4, 19, 9, 0),
        created_at=utc_dt(2026, 4, 19, 8, 30),
        updated_at=utc_dt(2026, 4, 19, 9, 0),
    )


class MomentServiceTest(unittest.IsolatedAsyncioTestCase):
    """动态服务异步逻辑测试。"""

    async def test_动态点赞首次成功后会增加点赞数(self) -> None:
        moment = build_moment()
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {}
        response = AsyncMock()

        with (
            patch("app.modules.moments.service.get_public_moment_or_404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.ensure_visitor_id", return_value="visitor-1"),
            patch("app.modules.moments.service.add_set_member_once", AsyncMock(return_value=True)),
        ):
            result = await like_moment(db, str(moment.id), request, response)

        self.assertEqual(moment.like_count, 1)
        self.assertEqual(result.like_count, 1)
        self.assertTrue(result.changed)
        db.flush.assert_awaited_once()

    async def test_动态重复点赞不会增加点赞数(self) -> None:
        moment = build_moment()
        moment.like_count = 3
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {"visitor_id": "visitor-1"}
        response = AsyncMock()

        with (
            patch("app.modules.moments.service.get_public_moment_or_404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.ensure_visitor_id", return_value="visitor-1"),
            patch("app.modules.moments.service.add_set_member_once", AsyncMock(return_value=False)),
        ):
            result = await like_moment(db, str(moment.id), request, response)

        self.assertEqual(moment.like_count, 3)
        self.assertEqual(result.like_count, 3)
        self.assertFalse(result.changed)
        db.flush.assert_not_awaited()

    async def test_动态取消点赞后会减少点赞数(self) -> None:
        moment = build_moment()
        moment.like_count = 3
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {"visitor_id": "visitor-1"}

        with (
            patch("app.modules.moments.service.get_public_moment_or_404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.remove_set_member", AsyncMock(return_value=True)),
        ):
            result = await unlike_moment(db, str(moment.id), request)

        self.assertEqual(moment.like_count, 2)
        self.assertEqual(result.like_count, 2)
        self.assertFalse(result.liked)
        self.assertTrue(result.changed)
        db.flush.assert_awaited_once()

    async def test_动态浏览首次记录后会增加浏览量(self) -> None:
        moment = build_moment()
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {}
        response = AsyncMock()

        with (
            patch("app.modules.moments.service.get_public_moment_or_404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.ensure_visitor_id", return_value="visitor-1"),
            patch("app.modules.moments.service.mark_key_once", AsyncMock(return_value=True)),
        ):
            result = await record_moment_view(db, str(moment.id), request, response)

        self.assertEqual(moment.view_count, 1)
        self.assertEqual(result.view_count, 1)
        self.assertTrue(result.changed)
        db.flush.assert_awaited_once()

    async def test_动态短时间重复浏览不会增加浏览量(self) -> None:
        moment = build_moment()
        moment.view_count = 5
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {"visitor_id": "visitor-1"}
        response = AsyncMock()

        with (
            patch("app.modules.moments.service.get_public_moment_or_404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.ensure_visitor_id", return_value="visitor-1"),
            patch("app.modules.moments.service.mark_key_once", AsyncMock(return_value=False)),
        ):
            result = await record_moment_view(db, str(moment.id), request, response)

        self.assertEqual(moment.view_count, 5)
        self.assertEqual(result.view_count, 5)
        self.assertFalse(result.changed)
        db.flush.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
