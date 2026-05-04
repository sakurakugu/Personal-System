"""动态服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.modules.moments.models import Moment
from app.modules.moments.schemas import MomentCreate
from app.modules.moments.service import like_moment, publish_moment, record_moment_view, unlike_moment
from app.modules.users.models import User, UserRole
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


def build_user(user_id=None) -> User:
    """构造测试用户。"""
    return User(
        id=user_id or generate_uuid7(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=UserRole.user,
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

    async def test_发布已有草稿时会原地发布并保留原动态_id(self) -> None:
        draft = build_moment()
        draft.is_published = False
        draft.published_at = None
        draft.title = "旧标题"
        draft.content = "旧内容"
        user = build_user(draft.user_id)
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalar_one=lambda: draft)
        now = utc_dt(2026, 5, 4, 12, 0)

        with (
            patch("app.modules.moments.service.get_draft", AsyncMock(return_value=draft)),
            patch("app.modules.moments.service.sync_moment_feed_item", AsyncMock()),
            patch("app.modules.moments.service.datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = now
            datetime_mock.timezone = timezone

            result = await publish_moment(
                db,
                MomentCreate(title="新标题", content="新内容"),
                user,
            )

        self.assertEqual(result.id, draft.id)
        self.assertTrue(draft.is_published)
        self.assertEqual(draft.published_at, now)
        self.assertEqual(draft.title, "新标题")
        self.assertEqual(draft.content, "新内容")
        db.delete.assert_not_awaited()
        self.assertEqual(db.flush.await_count, 2)


if __name__ == "__main__":
    unittest.main()
