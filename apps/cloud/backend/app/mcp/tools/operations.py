"""MCP 操作日志管理工具。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.mcp.context import MCP调用上下文
from app.mcp.operation_log import 列出最近操作, 撤销操作, 获取操作详情
from app.mcp.registry import MCP工具定义, 注册工具


class 最近操作参数(BaseModel):
    """最近操作列表参数。"""

    limit: int = Field(default=20, ge=1, le=100, description="返回条数")


class 操作ID参数(BaseModel):
    """操作 ID 参数。"""

    operation_id: str = Field(description="MCP 操作日志 ID")


def _获取MCP会话(context: MCP调用上下文):
    """获取当前 MCP 运行时数据库会话。"""
    if context.db is None:
        raise RuntimeError("MCP 工具缺少数据库会话")
    return context.db


async def operations_list_recent(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查看最近 MCP 操作。"""
    body = 最近操作参数.model_validate(args)
    return await 列出最近操作(_获取MCP会话(context), context.user, limit=body.limit)


async def operations_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查看 MCP 操作详情。"""
    body = 操作ID参数.model_validate(args)
    return await 获取操作详情(_获取MCP会话(context), context.user, body.operation_id)


async def operations_undo(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """撤销一次可撤销 MCP 操作。"""
    body = 操作ID参数.model_validate(args)
    return await 撤销操作(
        _获取MCP会话(context),
        context.user,
        operation_id=body.operation_id,
        device_session=context.device_session,
    )


注册工具(
    MCP工具定义(
        name="operations.list_recent",
        description="查看当前用户最近的 MCP 写操作和撤销状态。",
        input_schema=最近操作参数.model_json_schema(),
        permission="readonly",
        handler=operations_list_recent,
    )
)

注册工具(
    MCP工具定义(
        name="operations.get",
        description="查看当前用户的一次 MCP 操作详情，包括输入摘要、快照和结果摘要。",
        input_schema=操作ID参数.model_json_schema(),
        permission="readonly",
        handler=operations_get,
    )
)

注册工具(
    MCP工具定义(
        name="operations.undo",
        description="撤销当前用户的一次可撤销 MCP 操作。只接受 operation_id，不接受自定义反向参数。",
        input_schema=操作ID参数.model_json_schema(),
        permission="full",
        handler=operations_undo,
    )
)
