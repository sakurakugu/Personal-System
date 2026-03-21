"""待办事项 CRUD 路由 – 仅限当前用户。

此模块提供待办事项管理接口，包括：
- 获取待办事项列表
- 创建待办事项
- 更新待办事项（状态、优先级等）
- 删除待办事项

所有操作仅影响当前登录用户的待办事项。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Todo, TodoStatus, User
from app.schemas.schemas import TodoCreate, TodoRead, TodoUpdate

# 创建路由器，前缀为 /todos，标签为 todos
router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[TodoRead])
async def list_todos(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    获取当前用户的待办事项列表。

    按优先级升序、创建时间倒序排列。

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        list[TodoRead]: 待办事项列表
    """
    result = await db.execute(
        select(Todo)
        .where(Todo.user_id == user.id)
        .order_by(Todo.priority.asc(), Todo.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(body: TodoCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
        priority=body.priority,
        due_date=body.due_date,
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
    result = await db.execute(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k == "status":
            v = TodoStatus(v)
        setattr(todo, k, v)
    await db.flush()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除待办事项。

    只能删除自己的待办事项。

    Args:
        todo_id: 待办事项 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 待办事项不存在
    """
    result = await db.execute(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    await db.delete(todo)
