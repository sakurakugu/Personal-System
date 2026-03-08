"""Todo CRUD routes – scoped to current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Todo, TodoStatus, User
from app.schemas.schemas import TodoCreate, TodoRead, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[TodoRead])
async def list_todos(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Todo)
        .where(Todo.user_id == user.id)
        .order_by(Todo.priority.asc(), Todo.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(body: TodoCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    result = await db.execute(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
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
    result = await db.execute(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    await db.delete(todo)
