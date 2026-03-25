"""待办事项 CRUD 路由 – 仅限当前用户。

此模块提供待办事项管理接口，包括：
- 获取待办事项列表（支持筛选、排序）
- 创建待办事项
- 更新待办事项
- 软删除/恢复待办事项
- 置顶切换
- 批量操作

所有操作仅影响当前登录用户的待办事项。
"""

from __future__ import annotations

from datetime import datetime, timezone


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import RecurrenceType, Todo, TodoStatus, User
from app.schemas.schemas import TodoCreate, TodoRead, TodoUpdate

# 创建路由器，前缀为 /todos，标签为 todos
router = APIRouter(prefix="/todos", tags=["todos"])


def _utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


@router.get("", response_model=list[TodoRead])
async def list_todos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    # 筛选参数
    status: str | None = Query(None, description="状态筛选: todo/in_progress/done"),
    is_deleted: bool = Query(False, description="是否显示已删除（回收站）"),
    is_pinned: bool | None = Query(None, description="置顶筛选"),
    # 排序参数
    sort_by: str = Query("is_pinned", description="排序字段: is_pinned/importance/urgency/start_date/end_date/created_at"),
    sort_desc: bool = Query(True, description="是否倒序"),
):
    """
    获取当前用户的待办事项列表。

    默认按置顶状态、创建时间倒序排列。

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话
        status: 状态筛选
        is_deleted: 是否显示已删除
        is_pinned: 置顶筛选
        sort_by: 排序字段
        sort_desc: 是否倒序

    Returns:
        list[TodoRead]: 待办事项列表
    """
    query = select(Todo).where(Todo.user_id == user.id, Todo.is_deleted == is_deleted)
    
    # 状态筛选
    if status:
        query = query.where(Todo.status == status)
    
    # 置顶筛选
    if is_pinned is not None:
        query = query.where(Todo.is_pinned == is_pinned)
    
    # 动态排序
    sort_column = getattr(Todo, sort_by, Todo.created_at)
    if sort_desc:
        query = query.order_by(desc(Todo.is_pinned), desc(sort_column), desc(Todo.created_at))
    else:
        query = query.order_by(desc(Todo.is_pinned), asc(sort_column), asc(Todo.created_at))
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    body: TodoCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建待办事项。

    Args:
        body: 待办事项创建数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        TodoRead: 创建的待办事项
    """
    todo = Todo(
        user_id=user.id,
        title=body.title,
        description=body.description,
        importance=body.importance,
        urgency=body.urgency,
        start_date=body.start_date,
        end_date=body.end_date,
        is_pinned=body.is_pinned,
        tags=body.tags,
        recurrence_type=RecurrenceType(body.recurrence_type),
        recurrence_interval=body.recurrence_interval,
        recurrence_count=body.recurrence_count,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo)
    return todo


@router.patch("/{todo_id}", response_model=TodoRead)
async def update_todo(
    todo_id: str,
    body: TodoUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新待办事项。

    只能更新自己的待办事项。

    Args:
        todo_id: 待办事项 ID
        body: 待办事项更新数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        TodoRead: 更新后的待办事项

    Raises:
        HTTPException: 404 - 待办事项不存在
    """
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    data = body.model_dump(exclude_unset=True)
    
    for k, v in data.items():
        if k == "status" and v is not None:
            v = TodoStatus(v)
        elif k == "recurrence_type" and v is not None:
            v = RecurrenceType(v)
        setattr(todo, k, v)
    
    await db.flush()
    await db.refresh(todo)
    return todo


@router.post("/{todo_id}/toggle-pin", response_model=TodoRead)
async def toggle_pin(
    todo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    切换待办事项置顶状态。

    Args:
        todo_id: 待办事项 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        TodoRead: 更新后的待办事项

    Raises:
        HTTPException: 404 - 待办事项不存在
    """
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    todo.is_pinned = not todo.is_pinned
    await db.flush()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除待办事项（软删除或永久删除）。

    Args:
        todo_id: 待办事项 ID
        permanent: 是否永久删除（默认软删除）
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 待办事项不存在
    """
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    if permanent:
        # 永久删除
        await db.delete(todo)
    else:
        # 软删除
        todo.is_deleted = True
        todo.deleted_at = _utcnow()
        await db.flush()


@router.post("/{todo_id}/restore", response_model=TodoRead)
async def restore_todo(
    todo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    从回收站恢复待办事项。

    Args:
        todo_id: 待办事项 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        TodoRead: 恢复后的待办事项

    Raises:
        HTTPException: 404 - 待办事项不存在
    """
    result = await db.execute(
        select(Todo).where(
            Todo.id == todo_id,
            Todo.user_id == user.id,
            Todo.is_deleted.is_(True)
        )
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在或未被删除")
    
    todo.is_deleted = False
    todo.deleted_at = None
    await db.flush()
    await db.refresh(todo)
    return todo
