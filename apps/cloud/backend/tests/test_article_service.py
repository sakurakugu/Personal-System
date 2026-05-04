"""文章服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.modules.articles.content import extract_title_from_markdown_first_line
from app.modules.articles.crud import delete_article, restore_article, update_article
from app.modules.articles.models import Article, ArticleStatus
from app.modules.articles.permissions import (
    can_user_read_article,
    can_user_see_article_in_blog,
)
from app.modules.articles.queries import (
    get_article_by_slug,
    get_related_and_random_articles,
    is_article_liked_by_visitor,
    like_article_by_slug,
    list_article_image_storage_keys,
    unlike_article_by_slug,
)
from app.modules.articles.schema import build_article_read_response
from app.modules.articles.schemas import ArticleMetaRead, ArticleUpdate
from app.modules.articles.search import build_article_search_clause
from app.modules.articles.workflow import (
    apply_article_status,
    apply_article_deleted_state,
    build_unique_slug,
    restore_article_deleted_state,
    sort_articles_for_navigation,
    touch_article_last_edited_at,
)
from app.modules.users.models import User, UserRole
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
        like_count=0,
        word_count=0,
        author_id=generate_uuid7(),
        category_id=None,
        is_deleted=False,
        deleted_at=None,
        published_at=None,
        created_at=now,
        last_edited_at=now,
        updated_at=now,
    )


class ArticleServiceTest(unittest.TestCase):
    """文章服务纯逻辑测试。"""

    def test_未登录时文章搜索仅匹配标题(self) -> None:
        条件 = build_article_search_clause("关键字", None)

        self.assertIsNotNone(条件)
        条件文本 = str(条件)
        self.assertIn("articles.title", 条件文本)
        self.assertNotIn("articles.excerpt", 条件文本)
        self.assertNotIn("articles.content", 条件文本)

    def test_登录后文章搜索会匹配标题摘要和正文(self) -> None:
        user = User(
            id=generate_uuid7(),
            username="user",
            email="user@example.com",
            password_hash="x",
            role=UserRole.user,
        )

        条件 = build_article_search_clause("关键字", user)

        self.assertIsNotNone(条件)
        条件文本 = str(条件)
        self.assertIn("articles.title", 条件文本)
        self.assertIn("articles.excerpt", 条件文本)
        self.assertIn("articles.content", 条件文本)

    def test_空搜索词不会生成查询条件(self) -> None:
        self.assertIsNone(build_article_search_clause("   ", None))

    def test_提取文章标题时会移除引用和标题标记(self) -> None:
        self.assertEqual(extract_title_from_markdown_first_line("> 引用标题"), "引用标题")
        self.assertEqual(extract_title_from_markdown_first_line("## 二级标题"), "二级标题")
        self.assertEqual(extract_title_from_markdown_first_line("> ## 组合标题 ##"), "组合标题")
        self.assertEqual(extract_title_from_markdown_first_line("\n\n  >   # 带空格标题  \n正文"), "带空格标题")

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

    def test_软删除与恢复会更新删除字段(self) -> None:
        article = build_article()
        deleted_time = utc_dt(2026, 3, 28, 16, 30)

        apply_article_deleted_state(article, now=deleted_time)
        self.assertTrue(article.is_deleted)
        self.assertEqual(article.deleted_at, deleted_time)

        restore_article_deleted_state(article)
        self.assertFalse(article.is_deleted)
        self.assertIsNone(article.deleted_at)

    def test_刷新最后编辑时间只会修改最后编辑字段(self) -> None:
        article = build_article()
        edit_time = utc_dt(2026, 3, 28, 17, 30)

        touch_article_last_edited_at(article, now=edit_time)

        self.assertEqual(article.last_edited_at, edit_time)
        self.assertEqual(article.updated_at, utc_dt(2026, 3, 28, 12, 0))

    def test_文章导航排序优先发布时间否则使用创建时间(self) -> None:
        第一篇 = build_article()
        第一篇.title = "第一篇"
        第一篇.slug = "first"
        第一篇.created_at = utc_dt(2026, 3, 28, 10, 0)
        第一篇.published_at = utc_dt(2026, 3, 28, 11, 0)

        第二篇 = build_article()
        第二篇.title = "第二篇"
        第二篇.slug = "second"
        第二篇.created_at = utc_dt(2026, 3, 28, 12, 0)
        第二篇.published_at = None

        第三篇 = build_article()
        第三篇.title = "第三篇"
        第三篇.slug = "third"
        第三篇.created_at = utc_dt(2026, 3, 28, 9, 0)
        第三篇.published_at = utc_dt(2026, 3, 28, 13, 0)

        排序结果 = sort_articles_for_navigation([第一篇, 第二篇, 第三篇])

        self.assertEqual([article.slug for article in 排序结果], ["third", "second", "first"])

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

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
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

    def test_文章元数据响应包含作者信息(self) -> None:
        article = build_article()
        article.author = User(
            id=article.author_id,
            username="author",
            nickname="作者昵称",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
            is_active=True,
            created_at=utc_dt(2026, 3, 28, 12, 0),
        )
        article.author.ensure_settings()
        article.tags = []

        response = ArticleMetaRead.model_validate(article)

        self.assertEqual(response.author.username, "author")
        self.assertEqual(response.author.nickname, "作者昵称")


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
            patch("app.modules.articles.crud.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.replace_article_tags", AsyncMock()) as replace_tags,
            patch("app.modules.articles.crud.sync_article_feed_item", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_feed_home_cache", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_blog_stats_cache", AsyncMock()),
            patch("app.modules.articles.crud.utcnow", return_value=edit_time),
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

    async def test_文章点赞首次成功后会增加点赞数(self) -> None:
        article = build_article()
        article.status = ArticleStatus.public
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {}
        response = AsyncMock()

        with (
            patch("app.modules.articles.queries.get_article_for_related", AsyncMock(return_value=article)),
            patch("app.modules.articles.queries.ensure_visitor_id", return_value="visitor-1"),
            patch("app.modules.articles.queries.add_set_member_once", AsyncMock(return_value=True)),
        ):
            result = await like_article_by_slug(
                db,
                article.slug,
                None,
                request,
                response,
            )

        self.assertEqual(article.like_count, 1)
        self.assertEqual(result.like_count, 1)
        self.assertTrue(result.changed)
        db.flush.assert_awaited_once()

    async def test_文章重复点赞不会增加点赞数(self) -> None:
        article = build_article()
        article.status = ArticleStatus.public
        article.like_count = 2
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {"visitor_id": "visitor-1"}
        response = AsyncMock()

        with (
            patch("app.modules.articles.queries.get_article_for_related", AsyncMock(return_value=article)),
            patch("app.modules.articles.queries.ensure_visitor_id", return_value="visitor-1"),
            patch("app.modules.articles.queries.add_set_member_once", AsyncMock(return_value=False)),
        ):
            result = await like_article_by_slug(
                db,
                article.slug,
                None,
                request,
                response,
            )

        self.assertEqual(article.like_count, 2)
        self.assertEqual(result.like_count, 2)
        self.assertFalse(result.changed)
        db.flush.assert_not_awaited()

    async def test_文章取消点赞后会减少点赞数(self) -> None:
        article = build_article()
        article.status = ArticleStatus.public
        article.like_count = 2
        db = AsyncMock()
        request = AsyncMock()
        request.cookies = {"visitor_id": "visitor-1"}

        with (
            patch("app.modules.articles.queries.get_article_for_related", AsyncMock(return_value=article)),
            patch("app.modules.articles.queries.remove_set_member", AsyncMock(return_value=True)),
        ):
            result = await unlike_article_by_slug(db, article.slug, None, request)

        self.assertEqual(article.like_count, 1)
        self.assertEqual(result.like_count, 1)
        self.assertFalse(result.liked)
        self.assertTrue(result.changed)
        db.flush.assert_awaited_once()

    async def test_文章可返回当前访客点赞状态(self) -> None:
        request = AsyncMock()
        request.cookies = {"visitor_id": "visitor-1"}

        with patch("app.modules.articles.queries.has_set_member", AsyncMock(return_value=True)):
            result = await is_article_liked_by_visitor(generate_uuid7(), request)

        self.assertTrue(result)

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
            patch("app.modules.articles.crud.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.sync_article_feed_item", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_feed_home_cache", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_blog_stats_cache", AsyncMock()),
            patch("app.modules.articles.crud.utcnow", return_value=edit_time),
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

    async def test_草稿空标题保存时会自动取正文首行作为标题(self) -> None:
        article = build_article()
        article.title = ""
        article.slug = f"draft-{article.id}"
        article.content = ""
        user = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        db = AsyncMock()
        edit_time = utc_dt(2026, 3, 28, 19, 15)

        with (
            patch("app.modules.articles.crud.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.build_available_article_slug", AsyncMock(return_value="zi-dong-biao-ti")),
            patch("app.modules.articles.crud.sync_article_feed_item", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_feed_home_cache", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_blog_stats_cache", AsyncMock()),
            patch("app.modules.articles.crud.utcnow", return_value=edit_time),
        ):
            result = await update_article(
                db,
                str(article.id),
                ArticleUpdate(title="   ", content="> ## 自动标题 ##\n\n正文"),
                user,
            )

        self.assertIs(result, article)
        self.assertEqual(article.title, "自动标题")
        self.assertEqual(article.slug, "zi-dong-biao-ti")

    async def test_获取文章图片对象键列表(self) -> None:
        article = build_article()
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: ["articles/a.avif", "articles/b.avif"])
        )

        result = await list_article_image_storage_keys(db, article.id)

        self.assertEqual(result, ["articles/a.avif", "articles/b.avif"])

    async def test_相关推荐接口会返回上一篇和下一篇(self) -> None:
        当前文章 = build_article()
        当前文章.title = "当前"
        当前文章.slug = "current"
        当前文章.status = ArticleStatus.public
        当前文章.created_at = utc_dt(2026, 3, 28, 12, 0)
        当前文章.published_at = utc_dt(2026, 3, 28, 12, 0)
        当前文章.view_count = 10
        当前文章.tags = []
        当前文章.category = None

        更新文章 = build_article()
        更新文章.title = "更新"
        更新文章.slug = "newer"
        更新文章.created_at = utc_dt(2026, 3, 28, 13, 0)
        更新文章.published_at = utc_dt(2026, 3, 28, 13, 0)
        更新文章.tags = []
        更新文章.category = None

        更早文章 = build_article()
        更早文章.title = "更早"
        更早文章.slug = "older"
        更早文章.created_at = utc_dt(2026, 3, 28, 11, 0)
        更早文章.published_at = utc_dt(2026, 3, 28, 11, 0)
        更早文章.tags = []
        更早文章.category = None

        db = AsyncMock()

        with (
            patch("app.modules.articles.queries.get_article_for_related", AsyncMock(return_value=当前文章)),
            patch(
                "app.modules.articles.queries.list_all_article_meta",
                AsyncMock(return_value=[当前文章, 更新文章, 更早文章]),
            ),
            patch("random.sample", return_value=[]),
        ):
            prev_article, next_article, related, random_articles = await get_related_and_random_articles(
                db,
                当前文章.slug,
                None,
            )

        self.assertEqual(prev_article.slug if prev_article else None, "newer")
        self.assertEqual(next_article.slug if next_article else None, "older")
        self.assertEqual(len(related), 2)
        self.assertEqual(random_articles, [])

    async def test_软删除文章会移入回收站并清理_feed(self) -> None:
        article = build_article()
        article.category_id = generate_uuid7()
        user = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        db = AsyncMock()

        with (
            patch("app.modules.articles.crud.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.delete_feed_item", AsyncMock()) as delete_feed_item_mock,
            patch("app.modules.articles.crud.invalidate_feed_home_cache", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_blog_stats_cache", AsyncMock()),
            patch("app.modules.articles.crud.utcnow", return_value=utc_dt(2026, 3, 28, 20, 0)),
        ):
            await delete_article(db, str(article.id), user, permanent=False)

        self.assertTrue(article.is_deleted)
        self.assertEqual(article.deleted_at, utc_dt(2026, 3, 28, 20, 0))
        delete_feed_item_mock.assert_awaited_once()
        db.flush.assert_awaited_once()
        db.commit.assert_not_awaited()

    async def test_恢复文章会离开回收站并重建_feed(self) -> None:
        article = build_article()
        article.is_deleted = True
        article.deleted_at = utc_dt(2026, 3, 28, 20, 0)
        article.status = ArticleStatus.public
        article.published_at = utc_dt(2026, 3, 28, 18, 0)
        article.category_id = generate_uuid7()
        user = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        db = AsyncMock()

        with (
            patch("app.modules.articles.crud.get_deleted_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.get_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.sync_article_feed_item", AsyncMock()) as sync_feed_item_mock,
            patch("app.modules.articles.crud.invalidate_feed_home_cache", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_blog_stats_cache", AsyncMock()),
        ):
            result = await restore_article(db, str(article.id), user)

        self.assertIs(result, article)
        self.assertFalse(article.is_deleted)
        self.assertIsNone(article.deleted_at)
        sync_feed_item_mock.assert_awaited_once_with(db, article)
        db.flush.assert_awaited_once()

    async def test_永久删除文章后会清理图片对象(self) -> None:
        article = build_article()
        article.is_deleted = True
        article.deleted_at = utc_dt(2026, 3, 28, 20, 0)
        user = User(
            id=article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=UserRole.user,
        )
        db = AsyncMock()

        with (
            patch("app.modules.articles.crud.get_deleted_article_or_404", AsyncMock(return_value=article)),
            patch("app.modules.articles.crud.list_article_image_storage_keys", AsyncMock(return_value=["a", "b"])),
            patch("app.modules.articles.crud.delete_feed_item", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_feed_home_cache", AsyncMock()),
            patch("app.modules.articles.crud.invalidate_blog_stats_cache", AsyncMock()),
            patch("app.modules.articles.crud.remove_objects_best_effort") as remove_objects_mock,
        ):
            await delete_article(db, str(article.id), user, permanent=True)

        db.delete.assert_awaited_once_with(article)
        db.commit.assert_awaited_once()
        remove_objects_mock.assert_called_once_with(["a", "b"])


if __name__ == "__main__":
    unittest.main()
