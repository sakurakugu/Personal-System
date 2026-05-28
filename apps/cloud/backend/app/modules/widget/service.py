"""桌面小工具服务。"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import 设备会话范围, 用户设备会话
from app.modules.todos.models import Todo, TodoStatus
from app.modules.todos.service import _刷新待办们重复状态
from app.modules.users.models import 用户
from app.modules.widget.schemas import WidgetPublicSummaryRead, WidgetSummaryRead, WidgetTodoSummaryItemRead


def 校验小工具访问范围(
    current_session: 用户设备会话 | SimpleNamespace | None,
) -> None:
    """校验桌面小工具接口访问范围。"""
    if current_session is None:
        return
    session_scope = getattr(current_session, "scope", None)
    if session_scope != 设备会话范围.full_client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前设备权限不足")


async def 获取小工具摘要(
    db: AsyncSession,
    *,
    user: 用户,
    limit: int = 5,
) -> WidgetSummaryRead:
    """获取桌面小工具摘要。"""
    safe_limit = max(1, min(limit, 20))
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)

    refresh_result = await db.execute(
        select(Todo).where(
            Todo.user_id == user.id,
            Todo.is_deleted.is_(False),
        )
    )
    await _刷新待办们重复状态(db, list(refresh_result.scalars().all()))

    aggregate_result = await db.execute(
        select(
            func.count(Todo.id).label("pending_count"),
            func.sum(case((Todo.is_pinned.is_(True), 1), else_=0)).label("pinned_count"),
            func.sum(
                case(
                    (
                        Todo.end_date.is_not(None) & (Todo.end_date < now),
                        1,
                    ),
                    else_=0,
                )
            ).label("overdue_count"),
            func.sum(
                case(
                    (
                        Todo.end_date.is_not(None)
                        & (Todo.end_date >= today_start)
                        & (Todo.end_date < tomorrow_start),
                        1,
                    ),
                    else_=0,
                )
            ).label("due_today_count"),
        ).where(
            Todo.user_id == user.id,
            Todo.is_deleted.is_(False),
            Todo.status == TodoStatus.todo,
        )
    )
    aggregate_row = aggregate_result.one()

    items_result = await db.execute(
        select(Todo)
        .where(
            Todo.user_id == user.id,
            Todo.is_deleted.is_(False),
            Todo.status == TodoStatus.todo,
        )
        .order_by(
            Todo.is_pinned.desc(),
            Todo.end_date.is_(None),
            Todo.end_date.asc(),
            Todo.importance.desc(),
            Todo.urgency.desc(),
            Todo.created_at.desc(),
        )
        .limit(safe_limit)
    )
    items = [
        WidgetTodoSummaryItemRead(
            id=todo.id,
            title=todo.title,
            is_pinned=todo.is_pinned,
            importance=todo.importance,
            urgency=todo.urgency,
            end_date=todo.end_date,
        )
        for todo in items_result.scalars().all()
    ]

    return WidgetSummaryRead(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        pending_count=int(aggregate_row.pending_count or 0),
        pinned_count=int(aggregate_row.pinned_count or 0),
        overdue_count=int(aggregate_row.overdue_count or 0),
        due_today_count=int(aggregate_row.due_today_count or 0),
        items=items,
    )


async def 获取公开小工具摘要(
    db: AsyncSession,
    *,
    limit: int = 5,
) -> WidgetPublicSummaryRead:
    """获取公开桌面小工具摘要。"""
    safe_limit = max(1, min(limit, 20))
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)

    aggregate_result = await db.execute(
        select(
            func.count(Todo.id).label("pending_count"),
            func.sum(case((Todo.is_pinned.is_(True), 1), else_=0)).label("pinned_count"),
            func.sum(
                case(
                    (
                        Todo.end_date.is_not(None) & (Todo.end_date < now),
                        1,
                    ),
                    else_=0,
                )
            ).label("overdue_count"),
            func.sum(
                case(
                    (
                        Todo.end_date.is_not(None)
                        & (Todo.end_date >= today_start)
                        & (Todo.end_date < tomorrow_start),
                        1,
                    ),
                    else_=0,
                )
            ).label("due_today_count"),
        ).where(
            Todo.is_deleted.is_(False),
            Todo.status == TodoStatus.todo,
        )
    )
    aggregate_row = aggregate_result.one()

    items_result = await db.execute(
        select(Todo)
        .where(
            Todo.is_deleted.is_(False),
            Todo.status == TodoStatus.todo,
        )
        .order_by(
            Todo.is_pinned.desc(),
            Todo.end_date.is_(None),
            Todo.end_date.asc(),
            Todo.importance.desc(),
            Todo.urgency.desc(),
            Todo.created_at.desc(),
        )
        .limit(safe_limit)
    )
    items = [
        WidgetTodoSummaryItemRead(
            id=todo.id,
            title=todo.title,
            is_pinned=todo.is_pinned,
            importance=todo.importance,
            urgency=todo.urgency,
            end_date=todo.end_date,
        )
        for todo in items_result.scalars().all()
    ]

    return WidgetPublicSummaryRead(
        pending_count=int(aggregate_row.pending_count or 0),
        pinned_count=int(aggregate_row.pinned_count or 0),
        overdue_count=int(aggregate_row.overdue_count or 0),
        due_today_count=int(aggregate_row.due_today_count or 0),
        items=items,
    )
