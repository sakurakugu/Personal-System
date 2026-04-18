"""动态模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import User
from app.modules.feed.models import FeedItemType
from app.modules.feed.service import delete_feed_item, sync_moment_feed_item
from app.modules.moments.models import Moment
from app.modules.moments.schemas import MomentCreate, MomentDraftRead, MomentDraftSave, MomentPublicRead, MomentRead
from app.schemas.shared import PaginatedResponse


def moment_query():
    """构建动态基础查询。"""
    return select(Moment).options(selectinload(Moment.user))


async def list_moments(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """获取已发布的动态列表。"""
    query = moment_query().where(Moment.is_published.is_(True)).order_by(Moment.published_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[MomentPublicRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_public_moment_or_404(db: AsyncSession, moment_id: str) -> Moment:
    """获取单个已发布动态。"""
    result = await db.execute(
        moment_query().where(
            Moment.id == moment_id,
            Moment.is_published.is_(True),
        )
    )
    moment = result.scalar_one_or_none()
    if moment is None:
        raise HTTPException(status_code=404, detail="动态不存在")
    return moment


async def get_draft(db: AsyncSession, user: User) -> Moment | None:
    """获取当前用户草稿。"""
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def save_draft(
    db: AsyncSession,
    body: MomentDraftSave,
    user: User,
) -> MomentDraftRead:
    """保存动态草稿。"""
    draft = await get_draft(db, user)
    if draft is not None:
        draft.title = body.title
        draft.content = body.content
        draft.updated_at = datetime.now(timezone.utc)
    else:
        draft = Moment(
            title=body.title,
            content=body.content,
            is_published=False,
            user_id=user.id,
        )
        db.add(draft)

    await db.flush()
    return MomentDraftRead.model_validate(draft)


async def publish_moment(
    db: AsyncSession,
    body: MomentCreate,
    user: User,
) -> MomentRead:
    """发布动态。"""
    draft = await get_draft(db, user)
    if draft is not None:
        await db.delete(draft)

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
    await sync_moment_feed_item(db, moment)
    await db.flush()

    result = await db.execute(moment_query().where(Moment.id == moment.id))
    return MomentRead.model_validate(result.scalar_one())


async def list_my_moments(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: User,
) -> PaginatedResponse:
    """获取当前用户已发布动态列表。"""
    query = (
        moment_query()
        .where(
            Moment.user_id == user.id,
            Moment.is_published.is_(True),
        )
        .order_by(Moment.published_at.desc())
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[MomentRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_moment_or_404(db: AsyncSession, moment_id: str) -> Moment:
    """获取单个动态。"""
    result = await db.execute(select(Moment).where(Moment.id == moment_id))
    moment = result.scalar_one_or_none()
    if moment is None:
        raise HTTPException(status_code=404, detail="动态不存在")
    return moment


def ensure_moment_delete_permission(moment: Moment, user: User) -> None:
    """校验动态删除权限。"""
    if moment.user_id == user.id:
        return
    if user.role.value in ("admin", "super_admin"):
        return
    raise HTTPException(status_code=403, detail="无权操作")


async def delete_moment(db: AsyncSession, moment_id: str, user: User) -> None:
    """删除动态。"""
    moment = await get_moment_or_404(db, moment_id)
    ensure_moment_delete_permission(moment, user)
    await delete_feed_item(db, FeedItemType.moment, moment.id)
    await db.delete(moment)


__all__ = [
    "delete_moment",
    "ensure_moment_delete_permission",
    "get_draft",
    "get_moment_or_404",
    "get_public_moment_or_404",
    "list_moments",
    "list_my_moments",
    "moment_query",
    "publish_moment",
    "save_draft",
]
