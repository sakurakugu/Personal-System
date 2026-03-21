"""动态（Moments）路由。"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Moment, User
from app.schemas.schemas import (
    MomentCreate,
    MomentDraftSave,
    MomentRead,
    MomentPublicRead,
    MomentDraftRead,
    PaginatedResponse,
)

router = APIRouter(prefix="/moments", tags=["moments"])


def _moment_query():
    return select(Moment).options(selectinload(Moment.user))


# ─────────────────────────────────────────────────────────────
# 公开接口（博客端）
# ─────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse)
async def list_moments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """获取已发布的动态列表（公开）"""
    q = _moment_query().where(
        Moment.is_published.is_(True)
    ).order_by(Moment.published_at.desc())

    # 总数
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().unique().all()

    return PaginatedResponse(
        items=[MomentPublicRead.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/public/{moment_id}", response_model=MomentPublicRead)
async def get_public_moment(moment_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个已发布动态详情（公开）"""
    result = await db.execute(
        _moment_query().where(
            Moment.id == moment_id,
            Moment.is_published.is_(True)
        )
    )
    moment = result.scalar_one_or_none()
    if not moment:
        raise HTTPException(status_code=404, detail="动态不存在")
    return moment


# ─────────────────────────────────────────────────────────────
# 需要登录的接口
# ─────────────────────────────────────────────────────────────

@router.get("/draft", response_model=MomentDraftRead | None)
async def get_draft(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的草稿（只有一个）"""
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()
    return draft


@router.put("/draft", response_model=MomentDraftRead)
async def save_draft(
    body: MomentDraftSave,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """保存草稿（每个用户只有一个草稿，自动覆盖）"""
    # 查找现有草稿
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()

    if draft:
        # 更新现有草稿
        draft.title = body.title
        draft.content = body.content
        draft.updated_at = datetime.now(timezone.utc)
    else:
        # 创建新草稿
        draft = Moment(
            title=body.title,
            content=body.content,
            is_published=False,
            user_id=user.id,
        )
        db.add(draft)

    await db.flush()
    return draft


@router.post("/publish", response_model=MomentRead, status_code=status.HTTP_201_CREATED)
async def publish_moment(
    body: MomentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发布动态"""
    # 如果有草稿，删除它
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()
    if draft:
        await db.delete(draft)

    # 创建已发布的动态
    now = datetime.now(timezone.utc)
    moment = Moment(
        title=body.title,
        content=body.content,
        is_published=True,
        user_id=user.id,
        published_at=now,
    )
    db.add(moment)
    await db.flush()

    # 重新加载关联数据
    result = await db.execute(_moment_query().where(Moment.id == moment.id))
    return result.scalar_one()


@router.get("/my/list", response_model=PaginatedResponse)
async def list_my_moments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户已发布的动态列表"""
    q = (
        _moment_query()
        .where(
            Moment.user_id == user.id,
            Moment.is_published.is_(True)
        )
        .order_by(Moment.published_at.desc())
    )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().unique().all()

    return PaginatedResponse(
        items=[MomentRead.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.delete("/{moment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_moment(
    moment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除动态（只能删除自己的，管理员可以删除任何人的）"""
    result = await db.execute(select(Moment).where(Moment.id == moment_id))
    moment = result.scalar_one_or_none()
    if not moment:
        raise HTTPException(status_code=404, detail="动态不存在")

    # 检查权限
    if moment.user_id != user.id and user.role.value not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="无权操作")

    await db.delete(moment)
