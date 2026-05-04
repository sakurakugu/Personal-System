"""动态图片服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.modules.moments.image import list_moment_images
from app.modules.moments.models import Moment, MomentImage
from app.modules.users.models import User, UserRole


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_user() -> User:
    """构造测试用户。"""
    return User(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=UserRole.user,
    )


def build_moment(user: User) -> Moment:
    """构造测试动态。"""
    now = utc_dt(2026, 5, 4, 10, 0)
    return Moment(
        id=uuid4(),
        title="图片动态",
        content="content",
        is_published=False,
        view_count=0,
        like_count=0,
        user_id=user.id,
        published_at=None,
        created_at=now,
        updated_at=now,
    )


class MomentImageServiceAsyncTest(unittest.IsolatedAsyncioTestCase):
    """动态图片服务异步逻辑测试。"""

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_列出动态图片会返回预览地址与缩略图(self, _mock_time) -> None:
        user = build_user()
        moment = build_moment(user)
        image = MomentImage(
            id=uuid4(),
            moment_id=moment.id,
            original_name="动态图.avif",
            storage_key="user/moments/demo.avif",
            size=2048,
            mime_type="image/avif",
            sort_order=0,
            created_at=utc_dt(2026, 5, 4, 10, 30),
        )
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: [image])
        )

        with patch("app.modules.moments.image.get_moment_or_404", AsyncMock(return_value=moment)):
            result = await list_moment_images(db, user, str(moment.id))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].original_name, "动态图.avif")
        self.assertEqual(result[0].url, "/files/user/moments/demo.avif")
        self.assertEqual(result[0].sort_order, 0)
        self.assertIn("signature=", result[0].preview_url)
        self.assertIsNotNone(result[0].thumbnail_url)
        assert result[0].thumbnail_url is not None
        self.assertIn("thumbnail_width=144", result[0].thumbnail_url)


if __name__ == "__main__":
    unittest.main()
