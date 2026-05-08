"""动态服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.modules.moments.models import Moment
from app.modules.moments.schemas import MomentCreate, MomentUpdate
from app.modules.moments.service import (
    应用动态删除状态,
    删除动态,
    点赞动态,
    发布动态,
    记录动态浏览,
    恢复动态,
    恢复动态删除状态,
    刷新动态最后编辑时间,
    un点赞动态,
    更新动态,
)
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
        is_deleted=False,
        deleted_at=None,
        published_at=utc_dt(2026, 4, 19, 9, 0),
        created_at=utc_dt(2026, 4, 19, 8, 30),
        last_edited_at=utc_dt(2026, 4, 19, 9, 0),
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

    async def test_软删除与恢复会更新删除字段(self) -> None:
        moment = build_moment()
        deleted_time = utc_dt(2026, 5, 4, 11, 0)

        应用动态删除状态(moment, now=deleted_time)
        self.assertTrue(moment.is_deleted)
        self.assertEqual(moment.deleted_at, deleted_time)

        恢复动态删除状态(moment)
        self.assertFalse(moment.is_deleted)
        self.assertIsNone(moment.deleted_at)

    async def test_动态点赞首次成功后会增加点赞数(self) -> None:
        moment = build_moment()
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {}
        response = AsyncMock()

        with (
            patch("app.modules.moments.service.获取公开动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.确保访客ID", return_value="visitor-1"),
            patch("app.modules.moments.service.单次添加集合成员", AsyncMock(return_value=True)),
        ):
            result = await 点赞动态(db, str(moment.id), request, response)

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
            patch("app.modules.moments.service.获取公开动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.确保访客ID", return_value="visitor-1"),
            patch("app.modules.moments.service.单次添加集合成员", AsyncMock(return_value=False)),
        ):
            result = await 点赞动态(db, str(moment.id), request, response)

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
            patch("app.modules.moments.service.获取公开动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.移除集合成员", AsyncMock(return_value=True)),
        ):
            result = await un点赞动态(db, str(moment.id), request)

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
            patch("app.modules.moments.service.获取公开动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.确保访客ID", return_value="visitor-1"),
            patch("app.modules.moments.service.单次标记键", AsyncMock(return_value=True)),
        ):
            result = await 记录动态浏览(db, str(moment.id), request, response)

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
            patch("app.modules.moments.service.获取公开动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.确保访客ID", return_value="visitor-1"),
            patch("app.modules.moments.service.单次标记键", AsyncMock(return_value=False)),
        ):
            result = await 记录动态浏览(db, str(moment.id), request, response)

        self.assertEqual(moment.view_count, 5)
        self.assertEqual(result.view_count, 5)
        self.assertFalse(result.changed)
        db.flush.assert_not_awaited()

    async def test_刷新最后编辑时间会写入指定时间(self) -> None:
        moment = build_moment()
        edit_time = utc_dt(2026, 5, 5, 12, 0)

        刷新动态最后编辑时间(moment, now=edit_time)

        self.assertEqual(moment.last_edited_at, edit_time)

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
            patch("app.modules.moments.service.获取草稿", AsyncMock(return_value=draft)),
            patch("app.modules.moments.service.同步动态Feed条目", AsyncMock()),
            patch("app.modules.moments.service.清除Feed首页缓存", AsyncMock()),
            patch("app.modules.moments.service.datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = now
            datetime_mock.timezone = timezone

            result = await 发布动态(
                db,
                MomentCreate(title="新标题", content="新内容"),
                user,
            )

        self.assertEqual(result.id, draft.id)
        self.assertTrue(draft.is_published)
        self.assertEqual(draft.published_at, now)
        self.assertEqual(draft.last_edited_at, now)
        self.assertEqual(draft.title, "新标题")
        self.assertEqual(draft.content, "新内容")
        db.delete.assert_not_awaited()
        self.assertEqual(db.flush.await_count, 2)

    async def test_更新已发布动态会刷新最后编辑时间(self) -> None:
        moment = build_moment()
        user = build_user(moment.user_id)
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalar_one=lambda: moment)
        edited_time = utc_dt(2026, 5, 5, 13, 0)

        with (
            patch("app.modules.moments.service.获取动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.同步动态Feed条目", AsyncMock()) as sync_feed_item_mock,
            patch("app.modules.moments.service.清除Feed首页缓存", AsyncMock()) as invalidate_cache_mock,
            patch("app.modules.moments.service.datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = edited_time
            datetime_mock.timezone = timezone

            result = await 更新动态(
                db,
                str(moment.id),
                MomentUpdate(title="新标题", content="新内容"),
                user,
            )

        self.assertEqual(result.id, moment.id)
        self.assertEqual(moment.title, "新标题")
        self.assertEqual(moment.content, "新内容")
        self.assertEqual(moment.last_edited_at, edited_time)
        sync_feed_item_mock.assert_awaited_once_with(db, moment)
        invalidate_cache_mock.assert_awaited_once()
        db.flush.assert_awaited_once()

    async def test_软删除动态会移入回收站(self) -> None:
        moment = build_moment()
        user = build_user(moment.user_id)
        db = AsyncMock()
        deleted_time = utc_dt(2026, 5, 4, 12, 30)

        with (
            patch("app.modules.moments.service.获取动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.删除Feed条目", AsyncMock()) as 删除Feed条目_mock,
            patch("app.modules.moments.service.清除Feed首页缓存", AsyncMock()),
            patch("app.modules.moments.service.datetime") as datetime_mock,
        ):
            datetime_mock.now.return_value = deleted_time
            datetime_mock.timezone = timezone
            await 删除动态(db, str(moment.id), user, permanent=False)

        self.assertTrue(moment.is_deleted)
        self.assertEqual(moment.deleted_at, deleted_time)
        删除Feed条目_mock.assert_awaited_once()
        db.flush.assert_awaited_once()
        db.commit.assert_not_awaited()

    async def test_恢复动态会离开回收站并重建_feed(self) -> None:
        moment = build_moment()
        moment.is_deleted = True
        moment.deleted_at = utc_dt(2026, 5, 4, 12, 30)
        user = build_user(moment.user_id)
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalar_one=lambda: moment)

        with (
            patch("app.modules.moments.service.获取已删动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.同步动态Feed条目", AsyncMock()) as sync_feed_item_mock,
            patch("app.modules.moments.service.清除Feed首页缓存", AsyncMock()),
        ):
            result = await 恢复动态(db, str(moment.id), user)

        self.assertEqual(result.id, moment.id)
        self.assertFalse(moment.is_deleted)
        self.assertIsNone(moment.deleted_at)
        sync_feed_item_mock.assert_awaited_once_with(db, moment)
        db.flush.assert_awaited_once()

    async def test_永久删除动态后会清理图片对象(self) -> None:
        moment = build_moment()
        moment.is_deleted = True
        moment.deleted_at = utc_dt(2026, 5, 4, 12, 30)
        user = build_user(moment.user_id)
        db = AsyncMock()

        with (
            patch("app.modules.moments.service.获取已删动态或404", AsyncMock(return_value=moment)),
            patch("app.modules.moments.service.列出动态图片存储键", AsyncMock(return_value=["a", "b"])),
            patch("app.modules.moments.service.删除Feed条目", AsyncMock()),
            patch("app.modules.moments.service.清除Feed首页缓存", AsyncMock()),
            patch("app.modules.moments.service.尽力删除多个对象") as remove_objects_mock,
        ):
            await 删除动态(db, str(moment.id), user, permanent=True)

        db.delete.assert_awaited_once_with(moment)
        db.commit.assert_awaited_once()
        remove_objects_mock.assert_called_once_with(["a", "b"])


if __name__ == "__main__":
    unittest.main()
