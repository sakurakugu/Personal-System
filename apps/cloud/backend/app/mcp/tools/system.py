"""系统相关 MCP 工具。"""

from __future__ import annotations

from typing import Any

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.system.service import get_system_status


async def system_ping(_args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """检查云端 MCP 是否可用。"""
    return {
        "ok": True,
        "source": context.source,
        "user_id": str(context.user.id),
    }


async def system_status(_args: dict[str, Any], _context: MCP调用上下文) -> dict[str, Any]:
    """读取云端系统状态快照。"""
    status = await get_system_status()
    return status.model_dump(mode="json")


注册工具(
    MCP工具定义(
        name="system.ping",
        description="检查个人系统云端 MCP 是否可用。",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        permission="readonly",
        handler=system_ping,
    )
)

注册工具(
    MCP工具定义(
        name="system.status",
        description="读取云端后端的系统状态快照，包括资源占用和健康状态。",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        permission="readonly",
        handler=system_status,
    )
)

