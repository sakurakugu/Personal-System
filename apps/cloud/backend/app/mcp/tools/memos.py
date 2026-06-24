"""备忘录相关 MCP 工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.memos.models import 备忘录
from app.modules.memos.schemas import 备忘录创建, 备忘录信息, 备忘录更新
from app.modules.memos.service import (
    get_memo_or_404,
    创建备忘录,
    列出备忘录,
    删除备忘录,
    恢复备忘录,
    更新备忘录,
    获取已删备忘录或404,
)

备忘录状态参数 = Literal["inbox", "processed", "archived", "dropped"]
备忘录来源参数 = Literal["manual", "wechat", "web", "share", "unknown"]


class 备忘录列表参数(BaseModel):
    """当前用户备忘录列表查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: 备忘录状态参数 | None = Field(default=None, description="备忘录状态")
    source: 备忘录来源参数 | None = Field(default=None, description="备忘录来源")
    keyword: str | None = Field(default=None, max_length=100, description="关键词")
    is_deleted: bool = Field(default=False, description="是否查询回收站")


class 备忘录ID参数(BaseModel):
    """单条备忘录 ID 参数。"""

    memo_id: str = Field(description="备忘录 ID")
    is_deleted: bool = Field(default=False, description="是否读取回收站备忘录")


class 备忘录更新参数(BaseModel):
    """备忘录更新参数。"""

    memo_id: str = Field(description="备忘录 ID")
    expected_updated_at: str = Field(description="调用方读取到的 updated_at")
    content: str | None = Field(default=None, min_length=1, description="备忘录正文")
    status: 备忘录状态参数 | None = Field(default=None, description="备忘录状态")
    source: 备忘录来源参数 | None = Field(default=None, description="备忘录来源")


def _获取MCP会话(context: MCP调用上下文):
    """获取当前 MCP 运行时数据库会话。"""
    if context.db is None:
        raise RuntimeError("MCP 工具缺少数据库会话")
    return context.db


def _解析时间戳(value: str) -> datetime:
    """解析 ISO 时间戳。"""
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expected_updated_at 格式无效") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _转UTC(value: datetime) -> datetime:
    """将数据库时间戳转为 UTC。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def 校验备忘录更新时间(actual: datetime, expected: str) -> None:
    """校验调用方读取的备忘录更新时间仍然有效。"""
    if _转UTC(actual) != _解析时间戳(expected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "备忘录已被更新，请重新读取后再修改",
                "current_updated_at": actual.isoformat(),
            },
        )


def _备忘录读取(item: 备忘录信息) -> dict[str, Any]:
    """将备忘录响应模型转为稳定 JSON。"""
    return item.model_dump(mode="json")


def _备忘录快照(memo: 备忘录) -> dict[str, Any]:
    """构建备忘录撤销快照。"""
    return {
        "id": str(memo.id),
        "content": memo.content,
        "status": memo.status.value,
        "source": memo.source.value,
        "converted_to_type": memo.converted_to_type,
        "converted_to_id": str(memo.converted_to_id) if memo.converted_to_id else None,
        "archived_at": memo.archived_at.isoformat() if memo.archived_at else None,
        "deleted_at": memo.deleted_at.isoformat() if memo.deleted_at else None,
        "created_at": memo.created_at.isoformat(),
        "updated_at": memo.updated_at.isoformat(),
    }


def _构建备忘录更新载荷(args: dict[str, Any]) -> 备忘录更新:
    """从 MCP 参数构建备忘录更新载荷。"""
    allowed = {"content", "status", "source"}
    payload = {key: value for key, value in args.items() if key in allowed}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少提供一个可更新的备忘录字段")
    return 备忘录更新.model_validate(payload)


async def memos_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查询当前用户备忘录列表。"""
    body = 备忘录列表参数.model_validate(args)
    response = await 列出备忘录(
        _获取MCP会话(context),
        context.user,
        page=body.page,
        page_size=body.page_size,
        status=body.status,
        source=body.source,
        keyword=body.keyword,
        is_deleted=body.is_deleted,
    )
    return {
        "items": [_备忘录读取(item) for item in response.items],
        "total": response.total,
        "page": response.page,
        "page_size": response.page_size,
        "pages": response.pages,
    }


async def memos_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取当前用户的一条备忘录详情。"""
    body = 备忘录ID参数.model_validate(args)
    db = _获取MCP会话(context)
    memo = (
        await 获取已删备忘录或404(db, context.user, body.memo_id)
        if body.is_deleted
        else await get_memo_or_404(db, context.user, body.memo_id)
    )
    return _备忘录快照(memo)


async def memos_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """创建备忘录。"""
    body = 备忘录创建.model_validate(args)
    db = _获取MCP会话(context)
    created = await 创建备忘录(db, context.user, body)
    memo = await get_memo_or_404(db, context.user, str(created.id))
    after = _备忘录快照(memo)
    return {
        "summary": f"已创建备忘录：{memo.content[:40]}",
        "target": {"type": "memo", "id": str(memo.id)},
        "undoable": True,
        "undo_tool_name": "memos.delete",
        "after": after,
        "data": _备忘录读取(created),
    }


async def memos_update(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """更新当前用户备忘录。"""
    body = 备忘录更新参数.model_validate(args)
    db = _获取MCP会话(context)
    memo = await get_memo_or_404(db, context.user, body.memo_id)
    校验备忘录更新时间(memo.updated_at, body.expected_updated_at)
    before = _备忘录快照(memo)
    updated = await 更新备忘录(db, context.user, body.memo_id, _构建备忘录更新载荷(args))
    after_memo = await get_memo_or_404(db, context.user, body.memo_id)
    return {
        "summary": f"已更新备忘录：{after_memo.content[:40]}",
        "target": {"type": "memo", "id": str(after_memo.id)},
        "undoable": True,
        "undo_tool_name": "memos.update",
        "before": before,
        "after": _备忘录快照(after_memo),
        "data": _备忘录读取(updated),
    }


async def memos_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """将当前用户备忘录移入回收站。"""
    body = 备忘录ID参数.model_validate(args)
    db = _获取MCP会话(context)
    memo = await get_memo_or_404(db, context.user, body.memo_id)
    before = _备忘录快照(memo)
    summary_text = memo.content[:40]
    await 删除备忘录(db, context.user, body.memo_id, permanent=False)
    deleted = await 获取已删备忘录或404(db, context.user, body.memo_id)
    return {
        "summary": f"已移入回收站：{summary_text}",
        "target": {"type": "memo", "id": str(deleted.id)},
        "undoable": True,
        "undo_tool_name": "memos.restore",
        "before": before,
        "after": _备忘录快照(deleted),
    }


async def memos_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复当前用户备忘录。"""
    body = 备忘录ID参数.model_validate(args)
    db = _获取MCP会话(context)
    before_memo = await 获取已删备忘录或404(db, context.user, body.memo_id)
    before = _备忘录快照(before_memo)
    restored = await 恢复备忘录(db, context.user, body.memo_id)
    after_memo = await get_memo_or_404(db, context.user, body.memo_id)
    return {
        "summary": f"已恢复备忘录：{after_memo.content[:40]}",
        "target": {"type": "memo", "id": str(after_memo.id)},
        "undoable": True,
        "undo_tool_name": "memos.delete",
        "before": before,
        "after": _备忘录快照(after_memo),
        "data": _备忘录读取(restored),
    }


注册工具(
    MCP工具定义(
        name="memos.list",
        description="查询当前用户备忘录列表，支持状态、来源、关键词和回收站筛选。",
        input_schema=备忘录列表参数.model_json_schema(),
        permission="readonly",
        handler=memos_list,
    )
)
注册工具(
    MCP工具定义(
        name="memos.get",
        description="读取当前用户的一条备忘录详情。",
        input_schema=备忘录ID参数.model_json_schema(),
        permission="readonly",
        handler=memos_get,
    )
)
注册工具(
    MCP工具定义(
        name="memos.create",
        description="为当前用户创建备忘录，可通过撤销软删除新建备忘录。",
        input_schema=备忘录创建.model_json_schema(),
        permission="full",
        handler=memos_create,
    )
)
注册工具(
    MCP工具定义(
        name="memos.update",
        description="更新当前用户备忘录的正文、状态或来源，必须提供 expected_updated_at。",
        input_schema=备忘录更新参数.model_json_schema(),
        permission="full",
        handler=memos_update,
    )
)
注册工具(
    MCP工具定义(
        name="memos.delete",
        description="将当前用户的一条备忘录移入回收站，不执行永久删除。",
        input_schema=备忘录ID参数.model_json_schema(),
        permission="full",
        handler=memos_delete,
    )
)
注册工具(
    MCP工具定义(
        name="memos.restore",
        description="从回收站恢复当前用户的一条备忘录。",
        input_schema=备忘录ID参数.model_json_schema(),
        permission="full",
        handler=memos_restore,
    )
)
