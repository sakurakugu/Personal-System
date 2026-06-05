"""MCP 工具注册表。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import importlib
from typing import Any, Literal

from app.mcp.context import MCP调用上下文

MCP工具权限 = Literal["readonly", "full"]
MCP工具处理器 = Callable[[dict[str, Any], MCP调用上下文], Awaitable[dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class MCP工具定义:
    """MCP 工具定义。"""

    name: str
    description: str
    input_schema: dict[str, Any]
    permission: MCP工具权限
    handler: MCP工具处理器


工具注册表: dict[str, MCP工具定义] = {}
_工具已加载 = False


def _确保工具已加载() -> None:
    """确保工具模块已经完成注册。"""
    global _工具已加载
    if _工具已加载:
        return
    importlib.import_module("app.mcp.tools")
    _工具已加载 = True


def 注册工具(tool: MCP工具定义) -> None:
    """注册单个 MCP 工具。"""
    工具注册表[tool.name] = tool


def 列出工具() -> list[MCP工具定义]:
    """列出所有 MCP 工具。"""
    _确保工具已加载()
    return list(工具注册表.values())


def 获取工具(name: str) -> MCP工具定义:
    """按名称获取 MCP 工具。"""
    _确保工具已加载()
    return 工具注册表[name]


def 构建OpenAI工具定义() -> list[dict[str, Any]]:
    """构建 OpenAI 兼容工具定义。"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name.replace(".", "__"),
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }
        for tool in 列出工具()
    ]


def 从OpenAI工具名解析(name: str) -> str:
    """将 OpenAI 函数名还原为 MCP 工具名。"""
    return name.replace("__", ".")
