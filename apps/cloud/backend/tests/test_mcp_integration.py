"""MCP 接入基础测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from uuid import uuid4

from fastapi import HTTPException

from app.mcp.registry import 从OpenAI工具名解析, 构建OpenAI工具定义
from app.mcp.models import MCP操作日志, MCP操作状态
from app.mcp.operation_log import _校验可撤销, _序列化操作日志, 构建撤销截止时间
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
        self.assertIn("operations__undo", tool_names)
        self.assertEqual(从OpenAI工具名解析("todos__create"), "todos.create")

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
