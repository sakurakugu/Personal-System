"""待办事项 CRUD 路由。"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.todos.schemas import TodoCreate, TodoRead, TodoTagRead, TodoUpdate
from app.modules.todos.service import (
    complete_todo as complete_todo_service,
    create_todo as create_todo_service,
    delete_todo as delete_todo_service,
    list_todo_tags as list_todo_tags_service,
    list_todos as list_todos_service,
    restore_todo as restore_todo_service,
    toggle_pin as toggle_pin_service,
    取消完成待办 as 取消完成待办_service,
    update_todo as update_todo_service,
)
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/tags", response_model=list[TodoTagRead])
async def list_todo_tags(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的待办标签列表。"""
    return await list_todo_tags_service(db, user)


@router.get("", response_model=list[TodoRead])
async def list_todos(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None, description="状态筛选: todo/done"),
    tag: str | None = Query(None, description="标签筛选"),
    is_deleted: bool = Query(False, description="是否显示已删除（回收站）"),
    is_pinned: bool | None = Query(None, description="置顶筛选"),
    sort_by: str = Query("is_pinned", description="排序字段: is_pinned/importance/urgency/start_date/end_date/created_at"),
    sort_desc: bool = Query(True, description="是否倒序"),
):
    """获取当前用户的待办事项列表。"""
    return await list_todos_service(
        db,
        user,
        status=status,
        tag=tag,
        is_deleted=is_deleted,
        is_pinned=is_pinned,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    body: TodoCreate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建待办事项。"""
    return await create_todo_service(db, user, body)


@router.patch("/{todo_id}", response_model=TodoRead)
async def update_todo(
    todo_id: str,
    body: TodoUpdate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新待办事项。"""
    return await update_todo_service(db, user, todo_id, body)


@router.post("/{todo_id}/toggle-pin", response_model=TodoRead)
async def toggle_pin(
    todo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """切换待办事项置顶状态。"""
    return await toggle_pin_service(db, user, todo_id)


@router.post("/{todo_id}/complete", response_model=TodoRead)
async def complete_todo(
    todo_id: str,
    occurred_on: date | None = Query(None, description="按本地日期记录完成，默认今天"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """完成待办事项，更新循环进度。"""
    return await complete_todo_service(db, user, todo_id, occurred_on=occurred_on)


@router.post("/{todo_id}/uncomplete", response_model=TodoRead)
async def 取消完成待办(
    todo_id: str,
    occurred_on: date | None = Query(None, description="按本地日期撤销完成，默认最近一次完成日期"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """撤销待办事项的完成记录。"""
    return await 取消完成待办_service(db, user, todo_id, occurred_on=occurred_on)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除待办事项（软删除或永久删除）。"""
    await delete_todo_service(db, user, todo_id, permanent=permanent)


@router.post("/{todo_id}/restore", response_model=TodoRead)
async def restore_todo(
    todo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """从回收站恢复待办事项。"""
    return await restore_todo_service(db, user, todo_id)
