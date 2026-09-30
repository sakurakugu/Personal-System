"""博客发布快照的隔离与并发保护测试。"""

import unittest
from unittest.mock import AsyncMock, patch
from time import perf_counter

from fastapi import HTTPException

from app.modules.articles.crud import 更新文章
from app.modules.articles.publication import 发布博客, 修改博客发布状态, 提交博客发布事务
from app.mcp.context import MCP调用上下文
from app.mcp.tools.articles import _提交博客MCP操作
from app.modules.articles.schemas import 博客发布请求, 文章更新
from app.modules.users.models import 用户, 用户角色
from app.modules.articles.models import 文章
from app.modules.articles.content import utcnow
from app.utils.uuid import generate_uuid7


def 构建文章() -> 文章:
    """构建未发布文章，供快照隔离测试使用。"""
    now = utcnow()
    return 文章(
        id=generate_uuid7(),
        author_id=generate_uuid7(),
        title="测试文章",
        slug="test-article",
        content="content",
        revision=1,
        word_count=0,
        tags=[],
        blog=None,
        category=None,
        is_deleted=False,
        created_at=now,
        last_edited_at=now,
        updated_at=now,
    )


class 博客发布测试(unittest.IsolatedAsyncioTestCase):
    """检查文章保存与显式发布各自影响的数据。"""

    async def asyncSetUp(self) -> None:
        self.article = 构建文章()
        self.user = 用户(
            id=self.article.author_id,
            username="author",
            email="author@example.com",
            password_hash="x",
            role=用户角色.user,
        )
        self.db = AsyncMock()
        for name in ("同步文章Feed条目", "清除Feed首页缓存", "清除博客统计缓存"):
            patcher = patch(f"app.modules.articles.publication.{name}", AsyncMock())
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch(
            "app.modules.articles.publication.获取我的文章", AsyncMock(return_value=self.article)
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_保存文章不修改快照_显式更新发布保留链接统计和首次发布时间(self) -> None:
        await 发布博客(self.db, str(self.article.id), 博客发布请求(expected_revision=1), self.user)
        blog = self.article.blog
        self.assertIsNotNone(blog)
        first_time = blog.published_at
        first_slug = blog.slug
        blog.view_count = 8
        blog.like_count = 3
        with patch("app.modules.articles.crud.获取文章或404", AsyncMock(return_value=self.article)):
            await 更新文章(
                self.db, str(self.article.id), 文章更新(title="新版", content="新版正文"), self.user
            )
        self.assertEqual(blog.title, "测试文章")
        self.assertEqual(blog.content, "content")
        self.assertTrue(self.article.has_unpublished_changes)
        await 发布博客(self.db, str(self.article.id), 博客发布请求(expected_revision=2), self.user)
        self.assertEqual(blog.title, "新版")
        self.assertEqual(blog.content, "新版正文")
        self.assertEqual(blog.version, 2)
        self.assertEqual(blog.source_revision, 2)
        self.assertEqual((blog.view_count, blog.like_count), (8, 3))
        self.assertEqual(blog.published_at, first_time)
        self.assertEqual(blog.slug, first_slug)
        self.assertFalse(self.article.has_unpublished_changes)

    async def test_过期文章版本拒绝发布且不生成快照(self) -> None:
        self.article.revision = 2
        with self.assertRaises(HTTPException) as result:
            await 发布博客(
                self.db, str(self.article.id), 博客发布请求(expected_revision=1), self.user
            )
        self.assertEqual(result.exception.status_code, 409)
        self.assertIsNone(self.article.blog)

    async def test_修改可见性和撤下不覆盖正文(self) -> None:
        await 发布博客(self.db, str(self.article.id), 博客发布请求(expected_revision=1), self.user)
        self.article.content = "未发布修改"
        await 修改博客发布状态(
            self.db, str(self.article.id), self.user, visibility="login_required"
        )
        self.assertEqual(self.article.blog.content, "content")
        self.assertEqual(self.article.blog.status, "login_required")
        await 修改博客发布状态(self.db, str(self.article.id), self.user)
        self.assertFalse(self.article.blog.is_published)
        self.assertEqual(self.article.blog.version, 1)
        self.assertEqual(self.article.blog.content, "content")

    async def test_提交成功后才刷新缓存(self) -> None:
        calls = []

        async def commit():
            calls.append("提交")

        async def clear_feed():
            calls.append("首页缓存")

        async def clear_stats():
            calls.append("统计缓存")

        self.db.commit.side_effect = commit
        with (
            patch("app.modules.articles.publication.清除Feed首页缓存", side_effect=clear_feed),
            patch("app.modules.articles.publication.清除博客统计缓存", side_effect=clear_stats),
        ):
            await 提交博客发布事务(self.db)
        self.assertEqual(calls, ["提交", "首页缓存", "统计缓存"])

    async def test_MCP日志写入失败时不提交发布事务(self) -> None:
        context = MCP调用上下文(user=self.user, device_session=None, source="test", db=self.db)
        result = {"summary": "已发布博客快照", "undoable": False}
        with patch("app.mcp.tools.articles.记录MCP操作成功", side_effect=RuntimeError("日志失败")):
            with self.assertRaisesRegex(RuntimeError, "日志失败"):
                await _提交博客MCP操作(context, "blogs.publish", {}, result, perf_counter())
        self.db.commit.assert_not_awaited()
        self.assertNotIn("_operation_logged", result)
