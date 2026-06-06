"""MCP 接入基础测试。"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import unittest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.mcp.registry import 从OpenAI工具名解析, 构建OpenAI工具定义
from app.mcp.runtime import _是否允许调用
from app.mcp.models import MCP操作日志, MCP操作状态
from app.mcp.operation_log import _校验可撤销, _序列化操作日志, 构建撤销截止时间, 撤销操作
from app.mcp.article_content import 定位正文片段, 替换正文片段, 构建正文摘要, 解析Markdown大纲, 计算片段哈希
from app.mcp.tools.stats import _构建活动趋势响应
from app.mcp.tools.articles import _校验最后编辑时间
from app.mcp.tools.media import 校验文娱更新时间
from app.mcp.tools.moments import 校验动态最后编辑时间
from app.modules.auth.device_models import 设备会话范围, 设备会话类型
from app.modules.auth.device_service import 校验设备权限范围


class MCP接入基础测试(unittest.TestCase):
    """MCP 设备权限和工具定义测试。"""

    def test_mcp_设备只接受_mcp_scope(self) -> None:
        """MCP 设备不能使用普通客户端 scope。"""
        校验设备权限范围(设备会话类型.mcp, 设备会话范围.mcp_readonly)
        校验设备权限范围(设备会话类型.mcp, 设备会话范围.mcp_full)
        with self.assertRaises(HTTPException):
            校验设备权限范围(设备会话类型.mcp, 设备会话范围.full_client)

    def test_普通设备不能使用_mcp_scope(self) -> None:
        """普通设备不能使用 MCP scope。"""
        校验设备权限范围(设备会话类型.desktop, 设备会话范围.full_client)
        with self.assertRaises(HTTPException):
            校验设备权限范围(设备会话类型.desktop, 设备会话范围.mcp_full)

    def test_openai_工具名会映射回_mcp_工具名(self) -> None:
        """OpenAI 函数名兼容 MCP 点分工具名。"""
        tools = 构建OpenAI工具定义()
        tool_names = {item["function"]["name"] for item in tools}
        self.assertIn("todos__create", tool_names)
        self.assertIn("articles__patch_content", tool_names)
        self.assertIn("operations__undo", tool_names)
        self.assertIn("stats__blog_overview", tool_names)
        self.assertIn("stats__content_overview", tool_names)
        self.assertIn("stats__activity_trend", tool_names)
        self.assertIn("moments__create", tool_names)
        self.assertIn("moments__update", tool_names)
        self.assertIn("media__list", tool_names)
        self.assertIn("media__facets", tool_names)
        self.assertIn("media__get", tool_names)
        self.assertIn("media__create", tool_names)
        self.assertIn("media__update_metadata", tool_names)
        self.assertIn("media__delete", tool_names)
        self.assertIn("media__restore", tool_names)
        self.assertEqual(从OpenAI工具名解析("todos__create"), "todos.create")
        self.assertEqual(从OpenAI工具名解析("articles__patch_content"), "articles.patch_content")
        self.assertEqual(从OpenAI工具名解析("stats__activity_trend"), "stats.activity_trend")
        self.assertEqual(从OpenAI工具名解析("moments__update"), "moments.update")
        self.assertEqual(从OpenAI工具名解析("media__facets"), "media.facets")
        self.assertEqual(从OpenAI工具名解析("media__create"), "media.create")
        self.assertEqual(从OpenAI工具名解析("media__update_metadata"), "media.update_metadata")

    def test_stats_工具都是只读权限(self) -> None:
        """统计工具只能作为只读工具注册。"""
        tools = {item["function"]["name"]: item["function"] for item in 构建OpenAI工具定义()}

        self.assertIn("start_date", tools["stats__activity_trend"]["parameters"].get("properties", {}))
        self.assertTrue(_是否允许调用(设备会话范围.mcp_readonly, "readonly"))
        self.assertTrue(_是否允许调用(设备会话范围.mcp_full, "readonly"))
        self.assertFalse(_是否允许调用(设备会话范围.mcp_readonly, "full"))

    def test_stats_活动趋势返回稳定补零结构(self) -> None:
        """活动趋势按日期和模块补零，方便 AI 稳定消费。"""
        article_day = date(2026, 6, 1)
        response = _构建活动趋势响应(
            {"articles": {article_day: 2}},
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 2),
            modules=["articles", "todos"],
        )

        self.assertEqual(response["start_date"], "2026-06-01")
        self.assertEqual(response["end_date"], "2026-06-02")
        self.assertEqual(response["totals"], {"articles": 2, "todos": 0})
        self.assertEqual(
            response["days"],
            [
                {"date": "2026-06-01", "counts": {"articles": 2, "todos": 0}},
                {"date": "2026-06-02", "counts": {"articles": 0, "todos": 0}},
            ],
        )

    def test_文章列表和摘要工具_schema_不包含正文(self) -> None:
        """文章列表和摘要工具入参不会要求正文，避免默认泄露正文。"""
        tools = {item["function"]["name"]: item["function"] for item in 构建OpenAI工具定义()}

        list_schema = tools["articles__list_mine"]["parameters"]
        summary_schema = tools["articles__get_summary"]["parameters"]

        self.assertNotIn("content", list_schema.get("properties", {}))
        self.assertNotIn("content", summary_schema.get("properties", {}))

    def test_文章大纲包含片段哈希且不返回正文(self) -> None:
        """Markdown 大纲只返回定位信息和哈希。"""
        content = "# 标题\n正文\n## 小节\n内容\n# 第二章\n结尾\n"

        outline = 解析Markdown大纲(content)

        self.assertEqual(outline[0]["heading_path"], ["标题"])
        self.assertEqual(outline[1]["heading_path"], ["标题", "小节"])
        self.assertIn("hash", outline[0])
        self.assertNotIn("content", outline[0])

    def test_文章片段定位和替换使用_hash_保护(self) -> None:
        """局部替换可按标题定位并计算稳定哈希。"""
        content = "# 标题\n正文\n## 小节\n旧内容\n# 第二章\n结尾\n"
        fragment = 定位正文片段(content, {"type": "heading", "heading_path": ["标题", "小节"]})

        self.assertEqual(fragment.content, "## 小节\n旧内容\n")
        self.assertEqual(计算片段哈希(fragment.content), 计算片段哈希("## 小节\n旧内容\n"))
        self.assertIn("新内容", 替换正文片段(content, fragment, "## 小节\n新内容\n"))

    def test_正文摘要可用于空片段撤销保护(self) -> None:
        """正文摘要包含全文哈希，可保护删除片段后的插回撤销。"""
        content = "# 标题\n正文\n"

        summary = 构建正文摘要(content)

        self.assertEqual(summary["hash"], 计算片段哈希(content))
        self.assertEqual(summary["length"], len(content))

    def test_文章最后编辑时间不一致会拒绝(self) -> None:
        """文章局部写入必须基于最新 last_edited_at。"""
        actual = datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc)

        with self.assertRaises(HTTPException):
            _校验最后编辑时间(actual, "2026-06-06T01:01:00+00:00")

    def test_动态更新工具要求最后编辑时间(self) -> None:
        """动态更新工具必须携带 last_edited_at 版本校验。"""
        tools = {item["function"]["name"]: item["function"] for item in 构建OpenAI工具定义()}

        update_schema = tools["moments__update"]["parameters"]

        self.assertIn("expected_last_edited_at", update_schema.get("required", []))

    def test_动态最后编辑时间不一致会拒绝(self) -> None:
        """动态普通写入必须基于最新 last_edited_at。"""
        actual = datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc)

        with self.assertRaises(HTTPException):
            校验动态最后编辑时间(actual, "2026-06-06T01:01:00+00:00")

    def test_文娱更新工具只开放低风险元信息字段(self) -> None:
        """文娱 MCP 更新开放公开可见性但不开放封面、资源和外部来源写入字段。"""
        tools = {item["function"]["name"]: item["function"] for item in 构建OpenAI工具定义()}

        update_schema = tools["media__update_metadata"]["parameters"]
        properties = update_schema.get("properties", {})

        self.assertIn("expected_updated_at", update_schema.get("required", []))
        self.assertIn("title", properties)
        self.assertIn("rating", properties)
        self.assertIn("is_visible", properties)
        self.assertNotIn("primary_cover_asset_id", properties)
        self.assertNotIn("assets", properties)
        self.assertNotIn("external_sources", properties)

    def test_文娱创建工具复用创建_schema(self) -> None:
        """文娱 MCP 创建工具复用手动创建字段。"""
        tools = {item["function"]["name"]: item["function"] for item in 构建OpenAI工具定义()}

        create_schema = tools["media__create"]["parameters"]
        properties = create_schema.get("properties", {})

        self.assertIn("title", create_schema.get("required", []))
        self.assertIn("media_type", create_schema.get("required", []))
        self.assertIn("status", create_schema.get("required", []))
        self.assertIn("summary", properties)
        self.assertIn("is_visible", properties)

    def test_文娱聚合工具包含筛选维度参数(self) -> None:
        """文娱聚合工具支持按类型读取标签统计并限制创作者数量。"""
        tools = {item["function"]["name"]: item["function"] for item in 构建OpenAI工具定义()}

        facets_schema = tools["media__facets"]["parameters"]
        properties = facets_schema.get("properties", {})

        self.assertIn("media_type", properties)
        self.assertIn("creator_keyword", properties)
        self.assertIn("creator_limit", properties)

    def test_文娱更新时间不一致会拒绝(self) -> None:
        """文娱元信息写入必须基于最新 updated_at。"""
        actual = datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc)

        with self.assertRaises(HTTPException):
            校验文娱更新时间(actual, "2026-06-06T01:01:00+00:00")

    def test_撤销截止时间只给可撤销操作(self) -> None:
        """只有可撤销操作会生成撤销截止时间。"""
        now = datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc)
        self.assertIsNone(构建撤销截止时间(undoable=False, now=now))
        self.assertEqual(构建撤销截止时间(undoable=True, now=now), now + timedelta(days=7))

    def test_操作日志序列化隐藏详情(self) -> None:
        """最近操作列表不返回完整快照。"""
        operation = MCP操作日志(
            id=uuid4(),
            user_id=uuid4(),
            tool_name="todos.create",
            status=MCP操作状态.success,
            target_type="todo",
            target_id=str(uuid4()),
            duration_ms=12,
            is_undoable=True,
            undoable_until=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
            created_at=datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc),
        )

        data = _序列化操作日志(operation, include_detail=False)

        self.assertTrue(data["undoable"])
        self.assertEqual(data["target"]["type"], "todo")
        self.assertNotIn("before", data)

    def test_已撤销操作不能再次撤销(self) -> None:
        """已撤销操作不能重复撤销。"""
        operation = MCP操作日志(
            user_id=uuid4(),
            tool_name="todos.create",
            status=MCP操作状态.undone,
            is_undoable=True,
            duration_ms=1,
            undone_at=datetime(2026, 6, 6, 1, 0, tzinfo=timezone.utc),
        )

        with self.assertRaises(HTTPException):
            _校验可撤销(operation)


class MCP动态撤销测试(unittest.IsolatedAsyncioTestCase):
    """MCP 动态撤销分发测试。"""

    async def test_动态更新撤销会调用快照恢复(self) -> None:
        """moments.update 撤销走服务端定义的快照恢复处理器。"""
        operation_id = str(uuid4())
        target_id = str(uuid4())
        user = SimpleNamespace(id=uuid4())
        operation = MCP操作日志(
            id=uuid4(),
            user_id=uuid4(),
            tool_name="moments.update",
            status=MCP操作状态.success,
            target_type="moment",
            target_id=target_id,
            before_json={"title": "旧标题", "content": "旧内容", "is_published": True},
            duration_ms=1,
            is_undoable=True,
            undoable_until=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
        )
        db = AsyncMock()
        db.add = lambda _value: None

        with (
            patch("app.mcp.operation_log._获取操作或404", AsyncMock(return_value=operation)),
            patch("app.mcp.operation_log._按快照恢复动态", AsyncMock()) as restore_mock,
        ):
            result = await 撤销操作(db, user, operation_id=operation_id, device_session=None)

        restore_mock.assert_awaited_once_with(db, user, target_id, operation.before_json)
        self.assertEqual(result["summary"], "已撤销动态更新")
        self.assertEqual(result["target"]["type"], "moment")


class MCP文娱撤销测试(unittest.IsolatedAsyncioTestCase):
    """MCP 文娱撤销分发测试。"""

    async def test_文娱创建撤销会软删除新建文娱(self) -> None:
        """media.create 撤销只软删除新建条目。"""
        operation_id = str(uuid4())
        target_id = str(uuid4())
        user = SimpleNamespace(id=uuid4())
        operation = MCP操作日志(
            id=uuid4(),
            user_id=uuid4(),
            tool_name="media.create",
            status=MCP操作状态.success,
            target_type="media",
            target_id=target_id,
            duration_ms=1,
            is_undoable=True,
            undoable_until=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
        )
        db = AsyncMock()
        db.add = lambda _value: None

        with (
            patch("app.mcp.operation_log._获取操作或404", AsyncMock(return_value=operation)),
            patch("app.mcp.operation_log.删除文娱", AsyncMock()) as delete_mock,
        ):
            result = await 撤销操作(db, user, operation_id=operation_id, device_session=None)

        delete_mock.assert_awaited_once_with(db, user, target_id, permanent=False)
        self.assertEqual(result["summary"], "已撤销文娱创建")
        self.assertEqual(result["target"]["type"], "media")

    async def test_文娱元信息更新撤销会调用文娱更新服务(self) -> None:
        """media.update_metadata 撤销走服务端定义的元信息快照。"""
        operation_id = str(uuid4())
        target_id = str(uuid4())
        user = SimpleNamespace(id=uuid4())
        operation = MCP操作日志(
            id=uuid4(),
            user_id=uuid4(),
            tool_name="media.update_metadata",
            status=MCP操作状态.success,
            target_type="media",
            target_id=target_id,
            before_json={"title": "旧标题", "status": "planned", "rating": 8, "tags": ["旧标签"]},
            duration_ms=1,
            is_undoable=True,
            undoable_until=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
        )
        db = AsyncMock()
        db.add = lambda _value: None

        with (
            patch("app.mcp.operation_log._获取操作或404", AsyncMock(return_value=operation)),
            patch("app.mcp.operation_log.更新文娱", AsyncMock()) as update_mock,
        ):
            result = await 撤销操作(db, user, operation_id=operation_id, device_session=None)

        update_mock.assert_awaited_once()
        self.assertEqual(update_mock.call_args.args[2], target_id)
        self.assertEqual(result["summary"], "已撤销文娱元信息更新")
        self.assertEqual(result["target"]["type"], "media")

    async def test_文娱删除撤销会恢复文娱(self) -> None:
        """media.delete 撤销只恢复软删除条目。"""
        operation_id = str(uuid4())
        target_id = str(uuid4())
        user = SimpleNamespace(id=uuid4())
        operation = MCP操作日志(
            id=uuid4(),
            user_id=uuid4(),
            tool_name="media.delete",
            status=MCP操作状态.success,
            target_type="media",
            target_id=target_id,
            duration_ms=1,
            is_undoable=True,
            undoable_until=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
        )
        db = AsyncMock()
        db.add = lambda _value: None

        with (
            patch("app.mcp.operation_log._获取操作或404", AsyncMock(return_value=operation)),
            patch("app.mcp.operation_log.恢复文娱", AsyncMock()) as restore_mock,
        ):
            result = await 撤销操作(db, user, operation_id=operation_id, device_session=None)

        restore_mock.assert_awaited_once_with(db, user, target_id)
        self.assertEqual(result["summary"], "已撤销文娱删除")
        self.assertEqual(result["target"]["type"], "media")

    async def test_文娱恢复撤销会再次软删除(self) -> None:
        """media.restore 撤销只执行软删除。"""
        operation_id = str(uuid4())
        target_id = str(uuid4())
        user = SimpleNamespace(id=uuid4())
        operation = MCP操作日志(
            id=uuid4(),
            user_id=uuid4(),
            tool_name="media.restore",
            status=MCP操作状态.success,
            target_type="media",
            target_id=target_id,
            duration_ms=1,
            is_undoable=True,
            undoable_until=datetime(2026, 6, 13, 1, 0, tzinfo=timezone.utc),
        )
        db = AsyncMock()
        db.add = lambda _value: None

        with (
            patch("app.mcp.operation_log._获取操作或404", AsyncMock(return_value=operation)),
            patch("app.mcp.operation_log.删除文娱", AsyncMock()) as delete_mock,
        ):
            result = await 撤销操作(db, user, operation_id=operation_id, device_session=None)

        delete_mock.assert_awaited_once_with(db, user, target_id, permanent=False)
        self.assertEqual(result["summary"], "已撤销文娱恢复")
        self.assertEqual(result["target"]["type"], "media")


if __name__ == "__main__":
    unittest.main()
