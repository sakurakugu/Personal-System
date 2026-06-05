"""待办相关 MCP 工具。"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.todos.schemas import TodoCreate, TodoRead, TodoUpdate
from app.modules.todos.service import (
    complete_todo,
    create_todo,
    delete_todo,
    get_todo_or_404,
    list_todos,
    restore_todo,
    update_todo,
    取消完成待办,
)
from app.shared.db.session import async_session_factory


class 待办列表参数(BaseModel):
    """待办列表查询参数。"""

    status: str | None = Field(default=None, description="状态筛选：todo 或 done")
    tag: str | None = Field(default=None, description="标签筛选")
    is_deleted: bool = Field(default=False, description="是否查询回收站")
    is_pinned: bool | None = Field(default=None, description="是否只查询置顶")
    sort_by: str = Field(default="is_pinned", description="排序字段")
    sort_desc: bool = Field(default=True, description="是否倒序")


class 待办ID参数(BaseModel):
    """单个待办 ID 参数。"""

    todo_id: str = Field(description="待办 ID")


class 待办完成参数(待办ID参数):
    """完成或撤销完成参数。"""

    occurred_on: date | None = Field(default=None, description="按本地日期记录，格式 YYYY-MM-DD")


def _待办读取(todo: Any) -> dict[str, Any]:
    """将待办 ORM 对象转为稳定 JSON。"""
    return TodoRead.model_validate(todo).model_dump(mode="json")


async def todos_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查询当前用户待办。"""
    body = 待办列表参数.model_validate(args)
    async with async_session_factory() as db:
        todos = await list_todos(
            db,
            context.user,
            status=body.status,
            tag=body.tag,
            is_deleted=body.is_deleted,
            is_pinned=body.is_pinned,
            sort_by=body.sort_by,
            sort_desc=body.sort_desc,
        )
        await db.commit()
        return {"items": [_待办读取(todo) for todo in todos], "total": len(todos)}


async def todos_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取单个待办详情。"""
    body = 待办ID参数.model_validate(args)
    async with async_session_factory() as db:
        todo = await get_todo_or_404(db, context.user, body.todo_id)
        await db.commit()
        return _待办读取(todo)


async def todos_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """创建待办。"""
    body = TodoCreate.model_validate(args)
    async with async_session_factory() as db:
        todo = await create_todo(db, context.user, body)
        await db.commit()
        return {
            "summary": f"已创建待办：{todo.title}",
            "target": {"type": "todo", "id": str(todo.id)},
            "data": _待办读取(todo),
        }


async def todos_update(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """更新待办。"""
    todo_id = str(args.get("todo_id") or "")
    if not todo_id:
        raise ValueError("缺少 todo_id")
    body = TodoUpdate.model_validate({key: value for key, value in args.items() if key != "todo_id"})
    async with async_session_factory() as db:
        todo = await update_todo(db, context.user, todo_id, body)
        await db.commit()
        return {
            "summary": f"已更新待办：{todo.title}",
            "target": {"type": "todo", "id": str(todo.id)},
            "data": _待办读取(todo),
        }


async def todos_complete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """完成待办。"""
    body = 待办完成参数.model_validate(args)
    async with async_session_factory() as db:
        todo = await complete_todo(db, context.user, body.todo_id, occurred_on=body.occurred_on)
        await db.commit()
        return {
            "summary": f"已完成待办：{todo.title}",
            "target": {"type": "todo", "id": str(todo.id)},
            "data": _待办读取(todo),
        }


async def todos_uncomplete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """撤销待办完成记录。"""
    body = 待办完成参数.model_validate(args)
    async with async_session_factory() as db:
        todo = await 取消完成待办(db, context.user, body.todo_id, occurred_on=body.occurred_on)
        await db.commit()
        return {
            "summary": f"已撤销待办完成：{todo.title}",
            "target": {"type": "todo", "id": str(todo.id)},
            "data": _待办读取(todo),
        }


async def todos_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """软删除待办。"""
    body = 待办ID参数.model_validate(args)
    async with async_session_factory() as db:
        todo = await get_todo_or_404(db, context.user, body.todo_id)
        title = todo.title
        target_id = str(todo.id)
        await delete_todo(db, context.user, body.todo_id, permanent=False)
        await db.commit()
        return {
            "summary": f"已移入回收站：{title}",
            "target": {"type": "todo", "id": target_id},
        }


async def todos_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复待办。"""
    body = 待办ID参数.model_validate(args)
    async with async_session_factory() as db:
        todo = await restore_todo(db, context.user, body.todo_id)
        await db.commit()
        return {
            "summary": f"已恢复待办：{todo.title}",
            "target": {"type": "todo", "id": str(todo.id)},
            "data": _待办读取(todo),
        }


注册工具(
    MCP工具定义(
        name="todos.list",
        description="查询当前用户的待办列表。",
        input_schema=待办列表参数.model_json_schema(),
        permission="readonly",
        handler=todos_list,
    )
)
注册工具(
    MCP工具定义(
        name="todos.get",
        description="读取当前用户的一条待办详情。",
        input_schema=待办ID参数.model_json_schema(),
        permission="readonly",
        handler=todos_get,
    )
)
注册工具(
    MCP工具定义(
        name="todos.create",
        description="为当前用户创建一条待办。",
        input_schema=TodoCreate.model_json_schema(),
        permission="full",
        handler=todos_create,
    )
)
注册工具(
    MCP工具定义(
        name="todos.update",
        description="更新当前用户的一条待办。必须提供 todo_id，其余字段按需提供。",
        input_schema={
            "type": "object",
            "properties": {"todo_id": {"type": "string"}, **TodoUpdate.model_json_schema()["properties"]},
            "required": ["todo_id"],
            "additionalProperties": False,
        },
        permission="full",
        handler=todos_update,
    )
)
注册工具(
    MCP工具定义(
        name="todos.complete",
        description="完成当前用户的一条待办，可选指定 occurred_on。",
        input_schema=待办完成参数.model_json_schema(),
        permission="full",
        handler=todos_complete,
    )
)
注册工具(
    MCP工具定义(
        name="todos.uncomplete",
        description="撤销当前用户一条待办的完成记录，可选指定 occurred_on。",
        input_schema=待办完成参数.model_json_schema(),
        permission="full",
        handler=todos_uncomplete,
    )
)
注册工具(
    MCP工具定义(
        name="todos.delete",
        description="将当前用户的一条待办移入回收站，不执行永久删除。",
        input_schema=待办ID参数.model_json_schema(),
        permission="full",
        handler=todos_delete,
    )
)
注册工具(
    MCP工具定义(
        name="todos.restore",
        description="从回收站恢复当前用户的一条待办。",
        input_schema=待办ID参数.model_json_schema(),
        permission="full",
        handler=todos_restore,
    )
)
