"""待办事项 CRUD 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import TodoCreate, TodoRead, TodoUpdate
from app.services.todo_service import (
    complete_todo as complete_todo_service,
    create_todo as create_todo_service,
    delete_todo as delete_todo_service,
    list_todos as list_todos_service,
    restore_todo as restore_todo_service,
    toggle_pin as toggle_pin_service,
    update_todo as update_todo_service,
)

# 创建路由器，前缀为 /todos，标签为 todos
router = APIRouter(prefix="/todos", tags=["todos"])

@router.get("", response_model=list[TodoRead])
async def list_todos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    # 筛选参数
    status: str | None = Query(None, description="状态筛选: todo/done"),
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
    return await list_todos_service(
        db,
        user,
        status=status,
        is_deleted=is_deleted,
        is_pinned=is_pinned,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


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
    return await create_todo_service(db, user, body)


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
    return await update_todo_service(db, user, todo_id, body)


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
    return await toggle_pin_service(db, user, todo_id)


@router.post("/{todo_id}/complete", response_model=TodoRead)
async def complete_todo(
    todo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    完成待办事项，更新循环进度。

    如果设置了 times_per_interval > 1，会自动增加 interval_progress。
    当 interval_progress 达到 times_per_interval 时，会自动重置进度并减少循环次数。

    Args:
        todo_id: 待办事项 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        TodoRead: 更新后的待办事项

    Raises:
        HTTPException: 404 - 待办事项不存在
    """
    return await complete_todo_service(db, user, todo_id)


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
    await delete_todo_service(db, user, todo_id, permanent=permanent)


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
    return await restore_todo_service(db, user, todo_id)
