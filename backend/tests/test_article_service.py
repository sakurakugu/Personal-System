"""文章服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.article import Article, ArticleStatus
from app.services.article_service import apply_article_status, build_unique_slug


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_article() -> Article:
    """构造测试文章。"""
    now = utc_dt(2026, 3, 28, 12, 0)
    return Article(
        id=uuid4(),
        title="测试文章",
        slug="test-article",
        content="content",
        status=ArticleStatus.draft,
        view_count=0,
        author_id=uuid4(),
        category_id=None,
        published_at=None,
        created_at=now,
        updated_at=now,
    )


class ArticleServiceTest(unittest.TestCase):
    """文章服务纯逻辑测试。"""

    def test_slug_发生冲突时会追加时间戳(self) -> None:
        slug = build_unique_slug(
            "hello-world",
            exists=True,
            now=utc_dt(2026, 3, 28, 13, 45),
        )

        self.assertEqual(slug, "hello-world-1774705500")

    def test_发布状态会自动补发布时间_切回草稿会清空发布时间(self) -> None:
        article = build_article()
        publish_time = utc_dt(2026, 3, 28, 14, 0)
        draft_time = utc_dt(2026, 3, 28, 15, 0)

        apply_article_status(article, ArticleStatus.published, now=publish_time)
        self.assertEqual(article.status, ArticleStatus.published)
        self.assertEqual(article.published_at, publish_time)

        apply_article_status(article, ArticleStatus.draft, now=draft_time)
        self.assertEqual(article.status, ArticleStatus.draft)
        self.assertIsNone(article.published_at)


if __name__ == "__main__":
    unittest.main()
