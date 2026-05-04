"""文章图片服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.modules.articles.image import list_article_images
from app.modules.articles.models import Article, ArticleImage, ArticleStatus
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


def build_article(user: User) -> Article:
    """构造测试文章。"""
    now = utc_dt(2026, 4, 11, 10, 0)
    return Article(
        id=uuid4(),
        title="图片测试文章",
        slug="image-test-article",
        content="content",
        excerpt=None,
        cover_url=None,
        status=ArticleStatus.private,
        view_count=0,
        like_count=0,
        author_id=user.id,
        category_id=None,
        is_deleted=False,
        deleted_at=None,
        published_at=None,
        created_at=now,
        last_edited_at=now,
        updated_at=now,
    )


class ArticleImageServiceAsyncTest(unittest.IsolatedAsyncioTestCase):
    """文章图片服务异步逻辑测试。"""

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_列出文章图片会返回可预览地址与缩略图(self, _mock_time) -> None:
        user = build_user()
        article = build_article(user)
        image = ArticleImage(
            id=uuid4(),
            article_id=article.id,
            original_name="封面图.avif",
            storage_key="user/articles/cover.avif",
            size=2048,
            mime_type="image/avif",
            created_at=utc_dt(2026, 4, 11, 10, 30),
        )
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: [image])
        )

        with patch("app.modules.articles.image.get_article_or_404", AsyncMock(return_value=article)):
            result = await list_article_images(db, user, str(article.id))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].original_name, "封面图.avif")
        self.assertEqual(result[0].url, "/files/user/articles/cover.avif")
        self.assertIn("signature=", result[0].preview_url)
        self.assertIsNotNone(result[0].thumbnail_url)
        assert result[0].thumbnail_url is not None
        self.assertIn("thumbnail_width=144", result[0].thumbnail_url)


if __name__ == "__main__":
    unittest.main()
