"""文章服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole
from app.services.article_service import (
    apply_article_status,
    build_unique_slug,
    can_user_read_article,
    can_user_see_article_in_blog,
)
from app.utils.uuid import generate_uuid7


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_article() -> Article:
    """构造测试文章。"""
    now = utc_dt(2026, 3, 28, 12, 0)
    return Article(
        id=generate_uuid7(),
        title="测试文章",
        slug="test-article",
        content="content",
        status=ArticleStatus.private,
        view_count=0,
        author_id=generate_uuid7(),
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

    def test_公开状态会自动补发布时间_切回私有会清空发布时间(self) -> None:
        article = build_article()
        publish_time = utc_dt(2026, 3, 28, 14, 0)
        private_time = utc_dt(2026, 3, 28, 15, 0)

        apply_article_status(article, ArticleStatus.public, now=publish_time)
        self.assertEqual(article.status, ArticleStatus.public)
        self.assertEqual(article.published_at, publish_time)

        apply_article_status(article, ArticleStatus.private, now=private_time)
        self.assertEqual(article.status, ArticleStatus.private)
        self.assertIsNone(article.published_at)

    def test_登录可见状态也会自动补发布时间(self) -> None:
        article = build_article()
        publish_time = utc_dt(2026, 3, 28, 16, 0)

        apply_article_status(article, ArticleStatus.login_required, now=publish_time)
        self.assertEqual(article.status, ArticleStatus.login_required)
        self.assertEqual(article.published_at, publish_time)

    def test_文章访问权限按状态生效(self) -> None:
        article = build_article()

        article.status = ArticleStatus.public
        self.assertTrue(can_user_read_article(article, None))

        article.status = ArticleStatus.login_required
        self.assertFalse(can_user_read_article(article, None))
        self.assertTrue(
            can_user_read_article(
                article,
                User(id=generate_uuid7(), username="user", email="u@example.com", password_hash="x", role=UserRole.user),
            )
        )

        article.status = ArticleStatus.private
        self.assertFalse(can_user_read_article(article, None))
        self.assertTrue(
            can_user_read_article(
                article,
                User(
                    id=article.author_id,
                    username="author",
                    email="author@example.com",
                    password_hash="x",
                    role=UserRole.user,
                ),
            )
        )

    def test_博客列表可见性仅包含公开_登录可见_以及作者自己的私有(self) -> None:
        article = build_article()
        作者 = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        其他用户 = User(
            id=generate_uuid7(),
            username="other",
            email="other@example.com",
            password_hash="x",
            role=UserRole.user,
        )

        article.status = ArticleStatus.public
        self.assertTrue(can_user_see_article_in_blog(article, None))
        self.assertTrue(can_user_see_article_in_blog(article, 其他用户))

        article.status = ArticleStatus.login_required
        self.assertFalse(can_user_see_article_in_blog(article, None))
        self.assertTrue(can_user_see_article_in_blog(article, 其他用户))

        article.status = ArticleStatus.private
        self.assertFalse(can_user_see_article_in_blog(article, None))
        self.assertFalse(can_user_see_article_in_blog(article, 其他用户))
        self.assertFalse(can_user_see_article_in_blog(article, 作者))

        作者.show_private_articles_on_home = True
        self.assertTrue(can_user_see_article_in_blog(article, 作者))


if __name__ == "__main__":
    unittest.main()
