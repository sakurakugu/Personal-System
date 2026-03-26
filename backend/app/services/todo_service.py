"""待办事项服务层。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import RecurrenceType, Todo, TodoStatus, TodoTag, TodoTagRelation, User
from app.schemas.schemas import TodoCreate, TodoTagRead, TodoUpdate


def _utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def _resolve_recurrence_type(value: str) -> RecurrenceType:
    """将字符串循环类型转换为枚举。"""
    return RecurrenceType(value)


def _normalize_recurrence_payload(
    recurrence_type: str,
    recurrence_interval: int,
    recurrence_count: int,
    times_per_interval: int,
) -> tuple[str, int, int, int]:
    """统一循环字段语义。"""
    if recurrence_type == "none":
        return recurrence_type, 1, 0, 1
    if recurrence_type != "custom":
        recurrence_interval = 1
    return recurrence_type, recurrence_interval, recurrence_count, times_per_interval


def _validate_progress(interval_progress: int, times_per_interval: int) -> None:
    """校验循环进度合法性。"""
    if interval_progress < 0 or interval_progress > times_per_interval:
        raise HTTPException(status_code=422, detail="当前周期进度不能大于每周期完成次数")


def _todo_detail_query():
    """构建待办详情查询。"""
    return select(Todo).options(selectinload(Todo.todo_tags))


async def _get_user_tags_by_names(db: AsyncSession, user_id: UUID, tag_names: list[str]) -> dict[str, TodoTag]:
    """按名称获取用户标签映射。"""
    if not tag_names:
        return {}

    result = await db.execute(
        select(TodoTag).where(
            TodoTag.user_id == user_id,
            TodoTag.name.in_(tag_names),
        )
    )
    tags = result.scalars().all()
    return {tag.name: tag for tag in tags}


async def _sync_todo_tags(db: AsyncSession, todo: Todo, tag_names: list[str] | None) -> None:
    """同步待办标签关联。"""
    normalized_names = tag_names or []
    if not normalized_names:
        todo.todo_tags = []
        return

    existing_tags = await _get_user_tags_by_names(db, todo.user_id, normalized_names)
    resolved_tags: list[TodoTag] = []

    for name in normalized_names:
        tag = existing_tags.get(name)
        if tag is None:
            tag = TodoTag(user_id=todo.user_id, name=name)
            db.add(tag)
            await db.flush()
            existing_tags[name] = tag
        resolved_tags.append(tag)

    todo.todo_tags = resolved_tags


def _apply_update_payload(todo: Todo, body: TodoUpdate) -> None:
    """将更新请求应用到待办对象。"""
    data = body.model_dump(exclude_unset=True)
    recurrence_type = data.get("recurrence_type", todo.recurrence_type)
    recurrence_interval = data.get("recurrence_interval", todo.recurrence_interval)
    recurrence_count = data.get("recurrence_count", todo.recurrence_count)
    times_per_interval = data.get("times_per_interval", todo.times_per_interval)
    normalized_type, normalized_interval, normalized_count, normalized_times = _normalize_recurrence_payload(
        recurrence_type,
        recurrence_interval,
        recurrence_count,
        times_per_interval,
    )
    data["recurrence_type"] = normalized_type
    data["recurrence_interval"] = normalized_interval
    data["recurrence_count"] = normalized_count
    data["times_per_interval"] = normalized_times
    interval_progress = data.get("interval_progress", todo.interval_progress)
    _validate_progress(interval_progress, normalized_times)

    for key, value in data.items():
        if key == "status" and value is not None:
            value = TodoStatus(value)
        elif key == "recurrence_type" and value is not None:
            value = _resolve_recurrence_type(value)
        setattr(todo, key, value)

    if normalized_type == "none":
        todo.interval_progress = 0
        todo.progress_reset_at = None


async def list_todos(
    db: AsyncSession,
    user: User,
    *,
    status: str | None,
    tag: str | None,
    is_deleted: bool,
    is_pinned: bool | None,
    sort_by: str,
    sort_desc: bool,
) -> list[Todo]:
    """获取当前用户的待办列表。"""
    query = _todo_detail_query().where(Todo.user_id == user.id, Todo.is_deleted == is_deleted)

    if status:
        query = query.where(Todo.status == status)

    if tag:
        query = query.where(Todo.todo_tags.any(TodoTag.name == tag))

    if is_pinned is not None:
        query = query.where(Todo.is_pinned == is_pinned)

    sort_column = getattr(Todo, sort_by, Todo.created_at)
    if sort_desc:
        query = query.order_by(desc(Todo.is_pinned), desc(sort_column), desc(Todo.created_at))
    else:
        query = query.order_by(desc(Todo.is_pinned), asc(sort_column), asc(Todo.created_at))

    result = await db.execute(query)
    return list(result.scalars().all())


async def list_todo_tags(db: AsyncSession, user: User) -> list[TodoTagRead]:
    """获取当前用户的待办标签列表和使用次数。"""
    result = await db.execute(
        select(
            TodoTag.name,
            func.count(TodoTagRelation.todo_id).label("count"),
        )
        .select_from(TodoTag)
        .join(TodoTagRelation, TodoTagRelation.tag_id == TodoTag.id)
        .join(Todo, Todo.id == TodoTagRelation.todo_id)
        .where(
            TodoTag.user_id == user.id,
            Todo.is_deleted.is_(False),
        )
        .group_by(TodoTag.id, TodoTag.name)
        .order_by(func.count(TodoTagRelation.todo_id).desc(), TodoTag.name.asc())
    )
    return [
        TodoTagRead(
            name=row.name,
            count=row._mapping["count"],
        )
        for row in result
    ]


async def get_todo_or_404(db: AsyncSession, user: User, todo_id: str) -> Todo:
    """获取当前用户的待办事项。"""
    result = await db.execute(_todo_detail_query().where(Todo.id == todo_id, Todo.user_id == user.id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    return todo


async def get_deleted_todo_or_404(db: AsyncSession, user: User, todo_id: str) -> Todo:
    """获取当前用户已删除的待办事项。"""
    result = await db.execute(
        _todo_detail_query().where(Todo.id == todo_id, Todo.user_id == user.id, Todo.is_deleted.is_(True))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在或未被删除")
    return todo


async def create_todo(db: AsyncSession, user: User, body: TodoCreate) -> Todo:
    """创建待办事项。"""
    recurrence_type, recurrence_interval, recurrence_count, times_per_interval = _normalize_recurrence_payload(
        body.recurrence_type,
        body.recurrence_interval,
        body.recurrence_count,
        body.times_per_interval,
    )
    todo = Todo(
        user_id=user.id,
        title=body.title,
        description=body.description,
        importance=body.importance,
        urgency=body.urgency,
        start_date=body.start_date,
        end_date=body.end_date,
        is_pinned=body.is_pinned,
        recurrence_type=_resolve_recurrence_type(recurrence_type),
        recurrence_interval=recurrence_interval,
        recurrence_count=recurrence_count,
        times_per_interval=times_per_interval,
    )
    db.add(todo)
    await db.flush()
    await _sync_todo_tags(db, todo, body.tags)
    await db.flush()
    return await get_todo_or_404(db, user, str(todo.id))


async def update_todo(db: AsyncSession, user: User, todo_id: str, body: TodoUpdate) -> Todo:
    """更新待办事项。"""
    todo = await get_todo_or_404(db, user, todo_id)
    _apply_update_payload(todo, body)
    if "tags" in body.model_fields_set:
        await _sync_todo_tags(db, todo, body.tags)
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


async def toggle_pin(db: AsyncSession, user: User, todo_id: str) -> Todo:
    """切换置顶状态。"""
    todo = await get_todo_or_404(db, user, todo_id)
    todo.is_pinned = not todo.is_pinned
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


def _calculate_next_reset_at(todo: Todo) -> datetime | None:
    """计算下一次进度重置时间。"""
    if todo.recurrence_type == "daily":
        return _utcnow() + timedelta(days=todo.recurrence_interval)
    if todo.recurrence_type == "weekly":
        return _utcnow() + timedelta(weeks=todo.recurrence_interval)
    if todo.recurrence_type == "monthly":
        return _utcnow() + timedelta(days=30 * todo.recurrence_interval)
    if todo.recurrence_type == "yearly":
        return _utcnow() + timedelta(days=365 * todo.recurrence_interval)
    return None


async def complete_todo(db: AsyncSession, user: User, todo_id: str) -> Todo:
    """完成待办事项并更新循环进度。"""
    todo = await get_todo_or_404(db, user, todo_id)

    if todo.recurrence_type == "none" or todo.times_per_interval <= 1:
        todo.status = TodoStatus.done
        todo.interval_progress = 0
        todo.progress_reset_at = None
    else:
        todo.interval_progress += 1

        if todo.interval_progress >= todo.times_per_interval:
            todo.interval_progress = 0
            todo.status = TodoStatus.done
            if todo.recurrence_count > 0:
                todo.recurrence_count -= 1
            todo.progress_reset_at = _calculate_next_reset_at(todo)
        else:
            todo.status = TodoStatus.todo

    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


async def delete_todo(db: AsyncSession, user: User, todo_id: str, *, permanent: bool) -> None:
    """删除待办事项。"""
    todo = await get_todo_or_404(db, user, todo_id)
    if permanent:
        await db.delete(todo)
        return

    todo.is_deleted = True
    todo.deleted_at = _utcnow()
    await db.flush()


async def restore_todo(db: AsyncSession, user: User, todo_id: str) -> Todo:
    """从回收站恢复待办事项。"""
    todo = await get_deleted_todo_or_404(db, user, todo_id)
    todo.is_deleted = False
    todo.deleted_at = None
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)
