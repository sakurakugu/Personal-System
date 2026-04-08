"""文章服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole
from app.services.article_schema_service import build_article_read_response
from app.services.article_service import (
    apply_article_status,
    build_unique_slug,
    can_user_read_article,
    can_user_see_article_in_blog,
    get_article_by_slug,
    touch_article_last_edited_at,
    update_article,
)
from app.schemas.article import ArticleUpdate
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
        last_edited_at=now,
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

    def test_刷新最后编辑时间只会修改最后编辑字段(self) -> None:
        article = build_article()
        edit_time = utc_dt(2026, 3, 28, 17, 30)

        touch_article_last_edited_at(article, now=edit_time)

        self.assertEqual(article.last_edited_at, edit_time)
        self.assertEqual(article.updated_at, utc_dt(2026, 3, 28, 12, 0))

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

        作者.ensure_settings().show_private_articles_on_home = True
        self.assertTrue(can_user_see_article_in_blog(article, 作者))

    @patch("app.services.file_url_service.time.time", return_value=1_700_000_000)
    def test_公开文章响应会为站内文件附加签名(self, _mock_time) -> None:
        article = build_article()
        article.content = '![图](/files/user-id/articles/demo.avif)'
        article.cover_url = "/files/user-id/articles/cover.avif"
        article.status = ArticleStatus.public
        article.author = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
            is_active=True,
            created_at=utc_dt(2026, 3, 28, 12, 0),
        )
        article.author.ensure_settings()
        article.tags = []

        response = build_article_read_response(article, sign_file_urls=True)

        self.assertIn("signature=", response.content)
        self.assertIn("expires=1700000900", response.content)
        self.assertIsNotNone(response.cover_url)
        assert response.cover_url is not None
        self.assertIn("signature=", response.cover_url)


class ArticleServiceAsyncTest(unittest.IsolatedAsyncioTestCase):
    """文章服务异步逻辑测试。"""

    async def test_仅修改标签也会刷新最后编辑时间(self) -> None:
        article = build_article()
        user = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        db = AsyncMock()
        edit_time = utc_dt(2026, 3, 28, 18, 0)

        with (
            patch("app.services.article_service.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.services.article_service.replace_article_tags", AsyncMock()) as replace_tags,
            patch("app.services.article_service.sync_article_feed_item", AsyncMock()),
            patch("app.services.article_service.utcnow", return_value=edit_time),
        ):
            result = await update_article(
                db,
                str(article.id),
                ArticleUpdate(tag_ids=[]),
                user,
            )

        self.assertIs(result, article)
        self.assertEqual(article.last_edited_at, edit_time)
        replace_tags.assert_awaited_once()

    async def test_浏览文章只增加浏览量不会刷新最后编辑时间(self) -> None:
        article = build_article()
        article.status = ArticleStatus.public
        article.view_count = 3
        article.last_edited_at = utc_dt(2026, 3, 28, 12, 30)
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: article)

        result = await get_article_by_slug(db, article.slug, None)

        self.assertIs(result, article)
        self.assertEqual(article.view_count, 4)
        self.assertEqual(article.last_edited_at, utc_dt(2026, 3, 28, 12, 30))
        db.flush.assert_awaited_once()

    async def test_草稿占位_slug_会在首次填写标题后刷新(self) -> None:
        article = build_article()
        article.title = ""
        article.slug = f"draft-{article.id}"
        user = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
        edit_time = utc_dt(2026, 3, 28, 19, 0)

        with (
            patch("app.services.article_service.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.services.article_service.sync_article_feed_item", AsyncMock()),
            patch("app.services.article_service.utcnow", return_value=edit_time),
        ):
            result = await update_article(
                db,
                str(article.id),
                ArticleUpdate(title="正式标题"),
                user,
            )

        self.assertIs(result, article)
        self.assertEqual(article.title, "正式标题")
        self.assertEqual(article.slug, "zheng-shi-biao-ti")


if __name__ == "__main__":
    unittest.main()
