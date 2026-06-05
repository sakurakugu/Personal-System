"""MCP 操作日志和撤销服务。"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.article_content import 定位正文片段, 替换正文片段, 构建正文摘要, 计算片段哈希
from app.mcp.models import MCP操作日志, MCP操作状态
from app.modules.auth.device_models import 用户设备会话
from app.modules.articles.schemas import 文章更新
from app.modules.articles.service import 删除文章, 获取我的文章, 更新文章
from app.modules.todos.schemas import TodoUpdate
from app.modules.todos.service import (
    complete_todo,
    delete_todo,
    restore_todo,
    update_todo,
    取消完成待办,
)
from app.modules.users.models import 用户

默认撤销有效天数 = 7


def _now() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def _提取目标(result: dict[str, Any]) -> tuple[str | None, str | None]:
    """从工具返回中提取目标对象。"""
    target = result.get("target")
    if not isinstance(target, dict):
        return None, None
    target_type = target.get("type")
    target_id = target.get("id")
    return (
        str(target_type) if target_type is not None else None,
        str(target_id) if target_id is not None else None,
    )


def _转为JSON数据(value: Any) -> Any:
    """将对象转换为 JSONB 可保存的数据。"""
    return jsonable_encoder(value)


def _解析日期(value: Any) -> date | None:
    """解析 MCP 参数中的本地日期。"""
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return None


def _构建文章元信息更新(before_json: dict[str, Any]) -> 文章更新:
    """从文章撤销快照构造元信息恢复载荷。"""
    return 文章更新(
        title=before_json.get("title"),
        excerpt=before_json.get("excerpt"),
        cover_url=before_json.get("cover_url"),
        status=before_json.get("status"),
        category_id=before_json.get("category_id"),
        tag_ids=before_json.get("tag_ids"),
    )


async def _撤销文章局部更新(db: AsyncSession, user: 用户, target_id: str, operation: MCP操作日志) -> None:
    """撤销文章局部正文更新。"""
    before_json = operation.before_json or {}
    after_json = operation.after_json or {}
    target = before_json.get("target")
    before_fragment = before_json.get("fragment")
    after_fragment = after_json.get("fragment")
    expected_after_hash = after_json.get("fragment_hash")
    after_summary = after_json.get("content_summary")
    if not isinstance(target, dict) or not isinstance(before_fragment, str) or not isinstance(after_fragment, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="操作缺少局部正文撤销快照")

    article = await 获取我的文章(db, target_id, user)
    if after_fragment == "":
        start_index = after_json.get("start_index")
        if not isinstance(start_index, int):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="操作缺少空片段撤销位置")
        if isinstance(after_summary, dict) and 构建正文摘要(article.content).get("hash") != after_summary.get("hash"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="文章正文已再次变化，无法安全撤销")
        restored_content = f"{article.content[:start_index]}{before_fragment}{article.content[start_index:]}"
        await 更新文章(db, target_id, 文章更新(content=restored_content), user)
        return

    try:
        current_fragment = 定位正文片段(article.content, target)
    except HTTPException:
        current_fragment = 定位正文片段(article.content, {"type": "text_anchor", "text": after_fragment})

    if expected_after_hash and 计算片段哈希(current_fragment.content) != expected_after_hash:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="文章片段已再次变化，无法安全撤销")

    restored_content = 替换正文片段(article.content, current_fragment, before_fragment)
    await 更新文章(db, target_id, 文章更新(content=restored_content), user)


def 构建撤销截止时间(*, undoable: bool, now: datetime | None = None) -> datetime | None:
    """构建默认撤销截止时间。"""
    if not undoable:
        return None
    return (now or _now()) + timedelta(days=默认撤销有效天数)


async def 记录MCP操作成功(
    db: AsyncSession,
    *,
    user: 用户,
    device_session: 用户设备会话 | None,
    tool_name: str,
    args_json: dict[str, Any],
    result_json: dict[str, Any],
    duration_ms: int,
) -> MCP操作日志 | None:
    """记录成功的 MCP 工具调用。"""
    target_type, target_id = _提取目标(result_json)
    is_undoable = bool(result_json.get("undoable"))
    operation = MCP操作日志(
        user_id=user.id,
        device_session_id=device_session.id if device_session else None,
        tool_name=tool_name,
        status=MCP操作状态.success,
        target_type=target_type,
        target_id=target_id,
        args_json=_转为JSON数据(args_json),
        before_json=_转为JSON数据(result_json.get("before")),
        after_json=_转为JSON数据(result_json.get("after")),
        result_json=_转为JSON数据(result_json),
        duration_ms=duration_ms,
        is_undoable=is_undoable,
        undo_tool_name=result_json.get("undo_tool_name"),
        undoable_until=构建撤销截止时间(undoable=is_undoable),
    )
    db.add(operation)
    await db.flush()
    result_json["operation_id"] = str(operation.id)
    if is_undoable:
        result_json["undoable_until"] = operation.undoable_until.isoformat() if operation.undoable_until else None
    result_json.pop("before", None)
    result_json.pop("after", None)
    result_json.pop("undo_tool_name", None)
    operation.result_json = _转为JSON数据(result_json)
    return operation


async def 记录MCP操作失败(
    db: AsyncSession,
    *,
    user: 用户,
    device_session: 用户设备会话 | None,
    tool_name: str,
    args_json: dict[str, Any],
    error_message: str,
    duration_ms: int,
) -> MCP操作日志:
    """记录失败的 MCP 工具调用。"""
    operation = MCP操作日志(
        user_id=user.id,
        device_session_id=device_session.id if device_session else None,
        tool_name=tool_name,
        status=MCP操作状态.failed,
        args_json=_转为JSON数据(args_json),
        error_message=error_message,
        duration_ms=duration_ms,
        is_undoable=False,
    )
    db.add(operation)
    await db.flush()
    return operation


def _序列化操作日志(operation: MCP操作日志, *, include_detail: bool) -> dict[str, Any]:
    """将操作日志转为 MCP 返回数据。"""
    data: dict[str, Any] = {
        "id": str(operation.id),
        "tool_name": operation.tool_name,
        "status": operation.status.value,
        "target": {"type": operation.target_type, "id": operation.target_id}
        if operation.target_type and operation.target_id
        else None,
        "duration_ms": operation.duration_ms,
        "undoable": operation.is_undoable and operation.undone_at is None,
        "undoable_until": operation.undoable_until.isoformat() if operation.undoable_until else None,
        "undone_at": operation.undone_at.isoformat() if operation.undone_at else None,
        "created_at": operation.created_at.isoformat(),
        "updated_at": operation.updated_at.isoformat(),
    }
    if include_detail:
        data.update(
            {
                "args": operation.args_json,
                "before": operation.before_json,
                "after": operation.after_json,
                "result": operation.result_json,
                "error_message": operation.error_message,
                "undo_tool_name": operation.undo_tool_name,
                "undone_by_operation_id": str(operation.undone_by_operation_id)
                if operation.undone_by_operation_id
                else None,
            }
        )
    return data


async def 列出最近操作(db: AsyncSession, user: 用户, *, limit: int) -> dict[str, Any]:
    """列出当前用户最近的 MCP 操作。"""
    safe_limit = min(max(limit, 1), 100)
    result = await db.execute(
        select(MCP操作日志)
        .where(MCP操作日志.user_id == user.id)
        .order_by(MCP操作日志.created_at.desc())
        .limit(safe_limit)
    )
    items = [_序列化操作日志(operation, include_detail=False) for operation in result.scalars().all()]
    return {"items": items, "total": len(items)}


async def 获取操作详情(db: AsyncSession, user: 用户, operation_id: str) -> dict[str, Any]:
    """读取当前用户的一条 MCP 操作日志。"""
    operation = await _获取操作或404(db, user, operation_id)
    return _序列化操作日志(operation, include_detail=True)


async def _获取操作或404(db: AsyncSession, user: 用户, operation_id: str) -> MCP操作日志:
    """获取当前用户的 MCP 操作日志。"""
    operation = await db.get(MCP操作日志, UUID(operation_id))
    if operation is None or operation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP 操作不存在")
    return operation


def _校验可撤销(operation: MCP操作日志) -> None:
    """校验操作当前是否允许撤销。"""
    if not operation.is_undoable:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该操作不可撤销")
    if operation.status != MCP操作状态.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有成功操作可以撤销")
    if operation.undone_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该操作已经撤销")
    if operation.undoable_until is not None and operation.undoable_until <= _now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该操作已超过撤销期限")


async def 撤销操作(
    db: AsyncSession,
    user: 用户,
    *,
    operation_id: str,
    device_session: 用户设备会话 | None,
) -> dict[str, Any]:
    """撤销一次可撤销的 MCP 操作。"""
    operation = await _获取操作或404(db, user, operation_id)
    _校验可撤销(operation)

    target_id = operation.target_id
    if not target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="操作缺少目标对象，无法撤销")

    if operation.tool_name == "todos.create":
        await delete_todo(db, user, target_id, permanent=False)
        summary = "已撤销待办创建"
    elif operation.tool_name == "todos.update":
        before_json = operation.before_json or {}
        await update_todo(db, user, target_id, TodoUpdate.model_validate(before_json))
        summary = "已撤销待办更新"
    elif operation.tool_name == "todos.complete":
        args_json = operation.args_json or {}
        await 取消完成待办(db, user, target_id, occurred_on=_解析日期(args_json.get("occurred_on")))
        summary = "已撤销待办完成"
    elif operation.tool_name == "todos.uncomplete":
        args_json = operation.args_json or {}
        await complete_todo(db, user, target_id, occurred_on=_解析日期(args_json.get("occurred_on")))
        summary = "已撤销待办取消完成"
    elif operation.tool_name == "todos.delete":
        await restore_todo(db, user, target_id)
        summary = "已撤销待办删除"
    elif operation.tool_name == "todos.restore":
        await delete_todo(db, user, target_id, permanent=False)
        summary = "已撤销待办恢复"
    elif operation.tool_name == "articles.create":
        await 删除文章(db, target_id, user, permanent=False)
        summary = "已撤销文章创建"
    elif operation.tool_name == "articles.update_metadata":
        before_json = operation.before_json or {}
        await 更新文章(db, target_id, _构建文章元信息更新(before_json), user)
        summary = "已撤销文章元信息更新"
    elif operation.tool_name == "articles.replace_content":
        before_json = operation.before_json or {}
        content = before_json.get("content")
        if not isinstance(content, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="操作缺少文章正文撤销快照")
        await 更新文章(db, target_id, 文章更新(content=content), user)
        summary = "已撤销文章全文替换"
    elif operation.tool_name == "articles.patch_content":
        await _撤销文章局部更新(db, user, target_id, operation)
        summary = "已撤销文章局部正文更新"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该工具暂未实现撤销")

    undo_operation = MCP操作日志(
        user_id=user.id,
        device_session_id=device_session.id if device_session else None,
        tool_name="operations.undo",
        status=MCP操作状态.success,
        target_type=operation.target_type,
        target_id=operation.target_id,
        args_json={"operation_id": operation_id},
        result_json={"undone_operation_id": str(operation.id), "summary": summary},
        duration_ms=0,
        is_undoable=False,
    )
    db.add(undo_operation)
    await db.flush()

    operation.status = MCP操作状态.undone
    operation.undone_at = _now()
    operation.undone_by_operation_id = undo_operation.id
    await db.flush()

    return {
        "_operation_logged": True,
        "operation_id": str(undo_operation.id),
        "undone_operation_id": str(operation.id),
        "summary": summary,
        "target": {"type": operation.target_type, "id": operation.target_id},
    }
