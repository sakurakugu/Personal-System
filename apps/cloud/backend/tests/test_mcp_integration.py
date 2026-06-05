"""MCP 接入基础测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from uuid import uuid4

from fastapi import HTTPException

from app.mcp.registry import 从OpenAI工具名解析, 构建OpenAI工具定义
from app.mcp.models import MCP操作日志, MCP操作状态
from app.mcp.operation_log import _校验可撤销, _序列化操作日志, 构建撤销截止时间
from app.mcp.article_content import 定位正文片段, 替换正文片段, 构建正文摘要, 解析Markdown大纲, 计算片段哈希
from app.mcp.tools.articles import _校验最后编辑时间
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
        self.assertEqual(从OpenAI工具名解析("todos__create"), "todos.create")
        self.assertEqual(从OpenAI工具名解析("articles__patch_content"), "articles.patch_content")

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


if __name__ == "__main__":
    unittest.main()
