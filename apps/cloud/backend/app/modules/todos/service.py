"""待办事项服务层。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import asc, delete as sql_delete, desc, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import 用户
from app.modules.todos.models import RecurrenceType, Todo, TodoCompletionEvent, TodoStatus, TodoTag, TodoTagRelation
from app.modules.todos.schemas import TodoCreate, TodoTagRead, TodoUpdate
from app.integrations.holiday.service import 最大向后查找天数, 是否工作日, 是否节假日
from app.shared.kernel.config import settings

回收站保留天数 = 90


def _utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def _获取已删待办过期时间(deleted_at: datetime | None) -> datetime | None:
    """返回回收站待办的自动清理时间。"""
    if deleted_at is None:
        return None
    return deleted_at + timedelta(days=回收站保留天数)


def _已删待办是否过期(deleted_at: datetime | None, *, now: datetime | None = None) -> bool:
    """判断回收站待办是否已超过保留期限。"""
    expire_at = _获取已删待办过期时间(deleted_at)
    if expire_at is None:
        return False
    return expire_at <= (now or _utcnow())


def _local_timezone():
    """返回应用业务统一使用的本地时区。"""
    return settings.app_timezone


def _to_local(dt: datetime) -> datetime:
    """将时间统一转换到本地时区。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_local_timezone())


def _local_day_start(dt: datetime) -> datetime:
    """返回本地时区当天零点。"""
    local_dt = _to_local(dt)
    return local_dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _local_today() -> date:
    """返回本地时区今天日期。"""
    return _local_day_start(_utcnow()).date()


def _本地日期转UTC起始(day: date) -> datetime:
    """将本地日期转换为对应零点的 UTC 时间。"""
    local_tz = _local_timezone()
    return datetime.combine(day, time.min, tzinfo=local_tz).astimezone(timezone.utc)


def _解析重复类型(value: str) -> RecurrenceType:
    """将字符串循环类型转换为枚举。"""
    return RecurrenceType(value)


def _recurrence_value(value: str | RecurrenceType) -> str:
    """返回循环类型的字符串值。"""
    if isinstance(value, RecurrenceType):
        return value.value
    return value


def _规范化重复载荷(
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


def _重复锚定日期(todo: Todo) -> date:
    """返回循环规则的本地锚点日期。"""
    return _local_day_start(todo.start_date or todo.created_at).date()


def _是否还有剩余重复(todo: Todo) -> bool:
    """判断循环任务是否还有后续周期。"""
    return _recurrence_value(todo.recurrence_type) != "none" and todo.recurrence_count != 0


def _该日重复是否活跃(todo: Todo, check_date: date) -> bool:
    """判断循环任务在指定本地日期是否处于激活周期。"""
    recurrence_type = _recurrence_value(todo.recurrence_type)
    if recurrence_type == "none":
        return False

    start_date = _重复锚定日期(todo)
    if check_date < start_date:
        return False

    interval = max(1, todo.recurrence_interval)
    diff_days = (check_date - start_date).days

    if recurrence_type == "daily":
        return diff_days % interval == 0
    if recurrence_type == "weekly":
        return check_date.weekday() == start_date.weekday() and (diff_days // 7) % interval == 0
    if recurrence_type == "monthly":
        if check_date.day != start_date.day:
            return False
        month_delta = (check_date.year - start_date.year) * 12 + (check_date.month - start_date.month)
        return month_delta >= 0 and month_delta % interval == 0
    if recurrence_type == "yearly":
        if (check_date.month, check_date.day) != (start_date.month, start_date.day):
            return False
        year_delta = check_date.year - start_date.year
        return year_delta >= 0 and year_delta % interval == 0
    if recurrence_type == "workday":
        return 是否工作日(check_date)
    if recurrence_type == "weekend":
        return check_date.weekday() >= 5
    if recurrence_type == "holiday":
        return 是否节假日(check_date)
    if recurrence_type == "custom":
        return diff_days % interval == 0
    return False


def _计算下次重置时间(todo: Todo, *, reference_at: datetime | None = None) -> datetime | None:
    """计算下一次进度重置时间。"""
    if not _是否还有剩余重复(todo):
        return None

    reference_date = _local_day_start(reference_at or _utcnow()).date()
    candidate_date = max(reference_date + timedelta(days=1), _重复锚定日期(todo))
    local_tz = _local_timezone()

    for _ in range(最大向后查找天数):
        if _该日重复是否活跃(todo, candidate_date):
            return datetime.combine(candidate_date, time.min, tzinfo=local_tz).astimezone(timezone.utc)
        candidate_date += timedelta(days=1)
    return None


def _同步待办重置计划(todo: Todo, *, reference_at: datetime | None = None) -> None:
    """按当前状态同步下一次周期重置时间。"""
    if todo.recurrence_type == "none":
        todo.interval_progress = 0
        todo.progress_reset_at = None
        return

    if not _是否还有剩余重复(todo):
        todo.progress_reset_at = None
        return

    if todo.status == TodoStatus.done or todo.interval_progress > 0:
        todo.progress_reset_at = _计算下次重置时间(todo, reference_at=reference_at)
        return

    todo.progress_reset_at = None


def _刷新待办重复状态(todo: Todo, *, now: datetime | None = None) -> bool:
    """按当前时间刷新循环待办的状态和周期进度。"""
    changed = False
    now = now or _utcnow()

    if todo.recurrence_type == "none":
        if todo.interval_progress != 0:
            todo.interval_progress = 0
            changed = True
        if todo.progress_reset_at is not None:
            todo.progress_reset_at = None
            changed = True
        return changed

    if not _是否还有剩余重复(todo):
        if todo.progress_reset_at is not None:
            todo.progress_reset_at = None
            changed = True
        return changed

    if todo.status == TodoStatus.todo and todo.interval_progress == 0 and todo.progress_reset_at is not None:
        todo.progress_reset_at = None
        changed = True

    if todo.progress_reset_at is None and (todo.status == TodoStatus.done or todo.interval_progress > 0):
        next_reset_at = _计算下次重置时间(todo, reference_at=todo.updated_at)
        if next_reset_at != todo.progress_reset_at:
            todo.progress_reset_at = next_reset_at
            changed = True

    if todo.progress_reset_at is not None and todo.progress_reset_at <= now:
        if todo.status != TodoStatus.todo:
            todo.status = TodoStatus.todo
            changed = True
        if todo.interval_progress != 0:
            todo.interval_progress = 0
            changed = True
        todo.progress_reset_at = None
        changed = True

    return changed


async def _刷新待办们重复状态(db: AsyncSession, todos: list[Todo]) -> None:
    """批量刷新循环待办的状态。"""
    changed = False
    for todo in todos:
        changed = _刷新待办重复状态(todo) or changed
    if changed:
        await db.flush()


async def _清除过期已删待办(db: AsyncSession, *, user_id: UUID, now: datetime | None = None) -> None:
    """清理超过保留期限的回收站待办。"""
    current_time = now or _utcnow()
    expire_before = current_time - timedelta(days=回收站保留天数)
    await db.execute(
        sql_delete(Todo).where(
            Todo.user_id == user_id,
            Todo.is_deleted.is_(True),
            Todo.deleted_at.is_not(None),
            Todo.deleted_at <= expire_before,
        )
    )


def _todo_detail_query():
    """构建待办详情查询。"""
    return select(Todo).options(selectinload(Todo.todo_tags))


async def _按名称获取用户标签(db: AsyncSession, user_id: UUID, tag_names: list[str]) -> dict[str, TodoTag]:
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


async def _确保待办标签已加载(db: AsyncSession, todo: Todo) -> None:
    """确保标签关系已加载，避免异步懒加载触发异常。"""
    if "todo_tags" in inspect(todo).unloaded:
        await db.refresh(todo, attribute_names=["todo_tags"])


async def _sync_todo_tags(db: AsyncSession, todo: Todo, tag_names: list[str] | None) -> None:
    """同步待办标签关联。"""
    await _确保待办标签已加载(db, todo)
    normalized_names = tag_names or []
    if not normalized_names:
        todo.todo_tags = []
        return

    existing_tags = await _按名称获取用户标签(db, todo.user_id, normalized_names)
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


async def _记录完成事件(
    db: AsyncSession,
    todo: Todo,
    *,
    delta: int,
    occurred_on: date,
    occurred_at: datetime | None = None,
) -> None:
    """记录待办完成历史事件。"""
    if delta == 0:
        return

    event = TodoCompletionEvent(
        user_id=todo.user_id,
        todo_id=todo.id,
        todo_title_snapshot=todo.title,
        occurred_on=occurred_on,
        occurred_at=occurred_at or _本地日期转UTC起始(occurred_on),
        delta=delta,
        target_count_snapshot=max(1, todo.times_per_interval),
    )
    db.add(event)


async def _获取日期完成净值(
    db: AsyncSession,
    *,
    user_id: UUID,
    todo_id: UUID,
    occurred_on: date,
) -> int:
    """获取指定待办在某天的净完成次数。"""
    result = await db.execute(
        select(func.coalesce(func.sum(TodoCompletionEvent.delta), 0)).where(
            TodoCompletionEvent.user_id == user_id,
            TodoCompletionEvent.todo_id == todo_id,
            TodoCompletionEvent.occurred_on == occurred_on,
        )
    )
    value = result.scalar_one() or 0
    return int(value)


async def _获取最近完成日(
    db: AsyncSession,
    *,
    user_id: UUID,
    todo_id: UUID,
) -> date | None:
    """获取指定待办最近一次仍有净完成记录的日期。"""
    result = await db.execute(
        select(TodoCompletionEvent.occurred_on)
        .where(
            TodoCompletionEvent.user_id == user_id,
            TodoCompletionEvent.todo_id == todo_id,
        )
        .group_by(TodoCompletionEvent.occurred_on)
        .having(func.sum(TodoCompletionEvent.delta) > 0)
        .order_by(TodoCompletionEvent.occurred_on.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _重置待办完成状态(todo: Todo) -> None:
    """将待办当前完成状态重置为未完成。"""
    if todo.recurrence_type != "none" and todo.status == TodoStatus.done and todo.recurrence_count >= 0:
        todo.recurrence_count += 1

    todo.status = TodoStatus.todo
    todo.interval_progress = 0
    todo.progress_reset_at = None


def _应用更新载荷(todo: Todo, body: TodoUpdate) -> None:
    """将更新请求应用到待办对象。"""
    data = body.model_dump(exclude_unset=True)
    data.pop("tags", None)
    recurrence_type = data.get("recurrence_type", todo.recurrence_type)
    recurrence_interval = data.get("recurrence_interval", todo.recurrence_interval)
    recurrence_count = data.get("recurrence_count", todo.recurrence_count)
    times_per_interval = data.get("times_per_interval", todo.times_per_interval)
    normalized_type, normalized_interval, normalized_count, normalized_times = _规范化重复载荷(
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
            value = _解析重复类型(value)
        setattr(todo, key, value)

    _同步待办重置计划(todo, reference_at=_utcnow())


async def list_todos(
    db: AsyncSession,
    user: 用户,
    *,
    status: str | None,
    tag: str | None,
    is_deleted: bool,
    is_pinned: bool | None,
    sort_by: str,
    sort_desc: bool,
) -> list[Todo]:
    """获取当前用户的待办列表。"""
    await _清除过期已删待办(db, user_id=user.id)
    query = _todo_detail_query().where(Todo.user_id == user.id, Todo.is_deleted == is_deleted)

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
    todos = list(result.scalars().all())
    await _刷新待办们重复状态(db, todos)
    if status:
        return [todo for todo in todos if todo.status.value == status]
    return todos


async def list_todo_tags(db: AsyncSession, user: 用户) -> list[TodoTagRead]:
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


async def get_todo_or_404(db: AsyncSession, user: 用户, todo_id: str) -> Todo:
    """获取当前用户的待办事项。"""
    await _清除过期已删待办(db, user_id=user.id)
    result = await db.execute(_todo_detail_query().where(Todo.id == todo_id, Todo.user_id == user.id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    if _刷新待办重复状态(todo):
        await db.flush()
    return todo


async def 获取已删待办或404(db: AsyncSession, user: 用户, todo_id: str) -> Todo:
    """获取当前用户已删除的待办事项。"""
    await _清除过期已删待办(db, user_id=user.id)
    result = await db.execute(
        _todo_detail_query().where(Todo.id == todo_id, Todo.user_id == user.id, Todo.is_deleted.is_(True))
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在或未被删除")
    if _刷新待办重复状态(todo):
        await db.flush()
    return todo


async def create_todo(db: AsyncSession, user: 用户, body: TodoCreate) -> Todo:
    """创建待办事项。"""
    recurrence_type, recurrence_interval, recurrence_count, times_per_interval = _规范化重复载荷(
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
        recurrence_type=_解析重复类型(recurrence_type),
        recurrence_interval=recurrence_interval,
        recurrence_count=recurrence_count,
        times_per_interval=times_per_interval,
    )
    db.add(todo)
    await db.flush()
    await _sync_todo_tags(db, todo, body.tags)
    await db.flush()
    return await get_todo_or_404(db, user, str(todo.id))


async def update_todo(db: AsyncSession, user: 用户, todo_id: str, body: TodoUpdate) -> Todo:
    """更新待办事项。"""
    todo = await get_todo_or_404(db, user, todo_id)
    _应用更新载荷(todo, body)
    if "tags" in body.model_fields_set:
        await _sync_todo_tags(db, todo, body.tags)
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


async def toggle_pin(db: AsyncSession, user: 用户, todo_id: str) -> Todo:
    """切换置顶状态。"""
    todo = await get_todo_or_404(db, user, todo_id)
    todo.is_pinned = not todo.is_pinned
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


def _apply_completion(todo: Todo, *, completed_at: datetime | None = None) -> None:
    """记录一次完成操作并更新循环状态。"""
    completed_at = completed_at or _utcnow()

    if todo.status == TodoStatus.done and (todo.progress_reset_at is None or todo.progress_reset_at > completed_at):
        return

    if todo.recurrence_type == "none" or todo.recurrence_count == 0:
        todo.status = TodoStatus.done
        todo.interval_progress = 0
        todo.progress_reset_at = None
        return

    todo.interval_progress += 1
    if todo.interval_progress >= todo.times_per_interval:
        todo.status = TodoStatus.done
        todo.interval_progress = 0
        if todo.recurrence_count > 0:
            todo.recurrence_count -= 1
    else:
        todo.status = TodoStatus.todo

    _同步待办重置计划(todo, reference_at=completed_at)


async def complete_todo(
    db: AsyncSession,
    user: 用户,
    todo_id: str,
    *,
    occurred_on: date | None = None,
) -> Todo:
    """完成待办事项并记录历史。"""
    todo = await get_todo_or_404(db, user, todo_id)
    target_day = occurred_on or _local_today()
    today = _local_today()
    if target_day > today:
        raise HTTPException(status_code=422, detail="不能记录未来日期的完成情况")

    if target_day == today:
        completed_at = _utcnow()
        before_state = (
            todo.status,
            todo.interval_progress,
            todo.recurrence_count,
            todo.progress_reset_at,
        )
        _apply_completion(todo, completed_at=completed_at)
        after_state = (
            todo.status,
            todo.interval_progress,
            todo.recurrence_count,
            todo.progress_reset_at,
        )
        if before_state != after_state:
            await _记录完成事件(db, todo, delta=1, occurred_on=target_day, occurred_at=completed_at)
    else:
        await _记录完成事件(db, todo, delta=1, occurred_on=target_day)
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


async def 取消完成待办(
    db: AsyncSession,
    user: 用户,
    todo_id: str,
    *,
    occurred_on: date | None = None,
) -> Todo:
    """撤销某一天的完成记录。"""
    todo = await get_todo_or_404(db, user, todo_id)
    should_reset_current_state = occurred_on is None
    target_day = occurred_on or await _获取最近完成日(db, user_id=user.id, todo_id=todo.id)
    if target_day is None:
        return todo

    today = _local_today()
    if target_day > today:
        raise HTTPException(status_code=422, detail="不能撤销未来日期的完成情况")

    net_count = await _获取日期完成净值(db, user_id=user.id, todo_id=todo.id, occurred_on=target_day)
    if net_count <= 0:
        return todo

    await _记录完成事件(db, todo, delta=-net_count, occurred_on=target_day)
    if should_reset_current_state or target_day == today:
        _重置待办完成状态(todo)
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)


async def delete_todo(db: AsyncSession, user: 用户, todo_id: str, *, permanent: bool) -> None:
    """删除待办事项。"""
    todo = await get_todo_or_404(db, user, todo_id)
    if permanent:
        await db.delete(todo)
        return

    todo.is_deleted = True
    todo.deleted_at = _utcnow()
    await db.flush()


async def restore_todo(db: AsyncSession, user: 用户, todo_id: str) -> Todo:
    """从回收站恢复待办事项。"""
    todo = await 获取已删待办或404(db, user, todo_id)
    todo.is_deleted = False
    todo.deleted_at = None
    await db.flush()
    return await get_todo_or_404(db, user, todo_id)
