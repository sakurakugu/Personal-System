"""MCP 接入基础测试。"""

from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.mcp.registry import 从OpenAI工具名解析, 构建OpenAI工具定义
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
        self.assertEqual(从OpenAI工具名解析("todos__create"), "todos.create")


if __name__ == "__main__":
    unittest.main()

