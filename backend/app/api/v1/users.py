"""用户资料路由。"""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_super_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import User, UserRole
from app.schemas.schemas import (
    PaginatedResponse,
    UserAdminUpdate,
    UserCreateByAdmin,
    UserPasswordReset,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


def _parse_user_role(role_value: str) -> UserRole:
    try:
        return UserRole(role_value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    keyword: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(User)
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(or_(User.username.ilike(kw), User.email.ilike(kw)))
    if role:
        q = q.where(User.role == _parse_user_role(role))
    if is_active is not None:
        q = q.where(User.is_active.is_(is_active))
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()
    return PaginatedResponse(
        items=[UserRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateByAdmin,
    _admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    exists = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username or email already taken")
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=_parse_user_role(body.role),
        bio=body.bio,
        avatar_url=body.avatar_url,
        is_active=body.is_active,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    body: UserAdminUpdate,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role == UserRole.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="Cannot modify another super admin")

    data = body.model_dump(exclude_unset=True)
    if target.id == admin.id and ("role" in data or "is_active" in data):
        raise HTTPException(status_code=400, detail="Cannot change your own role or active status")

    if "username" in data and data["username"] != target.username:
        exists = await db.execute(
            select(User).where(User.username == data["username"], User.id != target.id)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken")
    if "email" in data and data["email"] != target.email:
        exists = await db.execute(select(User).where(User.email == data["email"], User.id != target.id))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already taken")

    if "role" in data:
        target.role = _parse_user_role(data.pop("role"))
    for k, v in data.items():
        setattr(target, k, v)
    await db.flush()
    await db.refresh(target)
    return target


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(
    user_id: UUID,
    body: UserPasswordReset,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role == UserRole.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="Cannot modify another super admin")
    target.password_hash = hash_password(body.password)
    await db.flush()
    return


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    await db.delete(target)
    await db.flush()
    return
