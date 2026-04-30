"""动态模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import User
from app.modules.feed.models import FeedItemType
from app.modules.feed.service import delete_feed_item, sync_moment_feed_item
from app.modules.moments.models import Moment
from app.modules.moments.schemas import (
    MomentCreate,
    MomentDraftRead,
    MomentDraftSave,
    MomentLikeRead,
    MomentPublicRead,
    MomentRead,
    MomentViewRead,
)
from app.shared.engagement import (
    add_set_member_once,
    ensure_visitor_id,
    get_visitor_id,
    has_set_member,
    mark_key_once,
    remove_set_member,
)
from app.shared.kernel.pagination import PaginatedResponse

_MOMENT_VIEW_DEDUP_SECONDS = 86400


def moment_query():
    """构建动态基础查询。"""
    return select(Moment).options(selectinload(Moment.user))


async def list_moments(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    visitor_id: str | None = None,
) -> PaginatedResponse:
    """获取已发布的动态列表。"""
    query = moment_query().where(Moment.is_published.is_(True)).order_by(Moment.published_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[await build_moment_public_read(item, visitor_id=visitor_id) for item in items],
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


async def build_moment_public_read(moment: Moment, *, visitor_id: str | None = None) -> MomentPublicRead:
    """构造公开动态响应，并附带点赞状态。"""
    liked = False
    if visitor_id:
        liked = await has_set_member(f"like:moment:{moment.id}", visitor_id)
    return MomentPublicRead.model_validate(moment).model_copy(update={"liked": liked})


async def like_moment(
    db: AsyncSession,
    moment_id: str,
    request: Request,
    response: Response,
) -> MomentLikeRead:
    """点赞动态，并基于匿名访客标识去重。"""
    moment = await get_public_moment_or_404(db, moment_id)
    visitor_id = ensure_visitor_id(request, response)
    changed = await add_set_member_once(f"like:moment:{moment.id}", visitor_id)
    if changed:
        moment.like_count += 1
        await db.flush()
    return MomentLikeRead(like_count=moment.like_count, changed=changed, liked=True)


async def unlike_moment(
    db: AsyncSession,
    moment_id: str,
    request: Request,
) -> MomentLikeRead:
    """取消点赞动态。"""
    moment = await get_public_moment_or_404(db, moment_id)
    visitor_id = get_visitor_id(request)
    if not visitor_id:
        return MomentLikeRead(like_count=moment.like_count, changed=False, liked=False)

    changed = await remove_set_member(f"like:moment:{moment.id}", visitor_id)
    if changed:
        moment.like_count = max(0, moment.like_count - 1)
        await db.flush()
    return MomentLikeRead(like_count=moment.like_count, changed=changed, liked=False)


async def record_moment_view(
    db: AsyncSession,
    moment_id: str,
    request: Request,
    response: Response,
) -> MomentViewRead:
    """记录动态浏览量，并对同一访客做轻量去重。"""
    moment = await get_public_moment_or_404(db, moment_id)
    visitor_id = ensure_visitor_id(request, response)
    changed = await mark_key_once(
        f"view:moment:{moment.id}:{visitor_id}",
        expire_seconds=_MOMENT_VIEW_DEDUP_SECONDS,
    )
    if changed:
        moment.view_count += 1
        await db.flush()
    return MomentViewRead(view_count=moment.view_count, changed=changed)


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
    "build_moment_public_read",
    "delete_moment",
    "ensure_moment_delete_permission",
    "get_draft",
    "get_moment_or_404",
    "get_public_moment_or_404",
    "like_moment",
    "list_moments",
    "list_my_moments",
    "moment_query",
    "publish_moment",
    "record_moment_view",
    "save_draft",
    "unlike_moment",
]
