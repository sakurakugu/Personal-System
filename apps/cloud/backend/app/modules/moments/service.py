"""动态模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import User
from app.modules.feed.models import FeedItemType
from app.modules.feed.service import 删除Feed条目, 清除Feed首页缓存, 同步动态Feed条目
from app.modules.moments.models import Moment, MomentImage
from app.modules.moments.permissions import 确保动态写入权限
from app.modules.moments.presentation import (
    构建动态草稿读取响应,
    构建动态公开读取响应,
    构建动态读取响应,
)
from app.modules.moments.schemas import (
    MomentCreate,
    MomentDraftRead,
    MomentDraftSave,
    MomentLikeRead,
    MomentPublicRead,
    MomentRead,
    MomentUpdate,
    MomentViewRead,
)
from app.shared.engagement import (
    包含集合成员,
    单次标记键,
    单次添加集合成员,
    确保访客ID,
    获取访客ID,
    移除集合成员,
)
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.storage.client import 尽力删除多个对象

_MOMENT_VIEW_DEDUP_SECONDS = 86400


def 动态查询():
    """构建动态基础查询。"""
    return select(Moment).options(selectinload(Moment.user), selectinload(Moment.images))


def 应用动态删除状态(moment: Moment, *, now: datetime | None = None) -> None:
    """将动态标记为已删除。"""
    moment.is_deleted = True
    moment.deleted_at = now or datetime.now(timezone.utc)


def 恢复动态删除状态(moment: Moment) -> None:
    """恢复动态删除状态。"""
    moment.is_deleted = False
    moment.deleted_at = None


def 刷新动态最后编辑时间(moment: Moment, *, now: datetime | None = None) -> None:
    """刷新动态最后编辑时间。"""
    moment.last_edited_at = now or datetime.now(timezone.utc)


async def 列出动态(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    visitor_id: str | None = None,
) -> PaginatedResponse:
    """获取已发布的动态列表。"""
    query = 动态查询().where(
        Moment.is_published.is_(True),
        Moment.is_deleted.is_(False),
    ).order_by(Moment.published_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[await 构建动态公开读取(item, visitor_id=visitor_id) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 获取公开动态或404(db: AsyncSession, moment_id: str) -> Moment:
    """获取单个已发布动态。"""
    result = await db.execute(
        动态查询().where(
            Moment.id == moment_id,
            Moment.is_published.is_(True),
            Moment.is_deleted.is_(False),
        )
    )
    moment = result.scalar_one_or_none()
    if moment is None:
        raise HTTPException(status_code=404, detail="动态不存在")
    return moment


async def 构建动态公开读取(moment: Moment, *, visitor_id: str | None = None) -> MomentPublicRead:
    """构造公开动态响应，并附带点赞状态。"""
    liked = False
    if visitor_id:
        liked = await 包含集合成员(f"like:moment:{moment.id}", visitor_id)
    return 构建动态公开读取响应(moment, liked=liked)


async def 点赞动态(
    db: AsyncSession,
    moment_id: str,
    request: Request,
    response: Response,
) -> MomentLikeRead:
    """点赞动态，并基于匿名访客标识去重。"""
    moment = await 获取公开动态或404(db, moment_id)
    visitor_id = 确保访客ID(request, response)
    changed = await 单次添加集合成员(f"like:moment:{moment.id}", visitor_id)
    if changed:
        moment.like_count += 1
        await db.flush()
    return MomentLikeRead(like_count=moment.like_count, changed=changed, liked=True)


async def un点赞动态(
    db: AsyncSession,
    moment_id: str,
    request: Request,
) -> MomentLikeRead:
    """取消点赞动态。"""
    moment = await 获取公开动态或404(db, moment_id)
    visitor_id = 获取访客ID(request)
    if not visitor_id:
        return MomentLikeRead(like_count=moment.like_count, changed=False, liked=False)

    changed = await 移除集合成员(f"like:moment:{moment.id}", visitor_id)
    if changed:
        moment.like_count = max(0, moment.like_count - 1)
        await db.flush()
    return MomentLikeRead(like_count=moment.like_count, changed=changed, liked=False)


async def 记录动态浏览(
    db: AsyncSession,
    moment_id: str,
    request: Request,
    response: Response,
) -> MomentViewRead:
    """记录动态浏览量，并对同一访客做轻量去重。"""
    moment = await 获取公开动态或404(db, moment_id)
    visitor_id = 确保访客ID(request, response)
    changed = await 单次标记键(
        f"view:moment:{moment.id}:{visitor_id}",
        expire_seconds=_MOMENT_VIEW_DEDUP_SECONDS,
    )
    if changed:
        moment.view_count += 1
        await db.flush()
    return MomentViewRead(view_count=moment.view_count, changed=changed)


async def 获取草稿(db: AsyncSession, user: User) -> Moment | None:
    """获取当前用户草稿。"""
    result = await db.execute(
        动态查询().where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
            Moment.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def 保存草稿(
    db: AsyncSession,
    body: MomentDraftSave,
    user: User,
) -> MomentDraftRead:
    """保存动态草稿。"""
    draft = await 获取草稿(db, user)
    if draft is not None:
        draft.title = body.title
        draft.content = body.content
        刷新动态最后编辑时间(draft)
    else:
        draft = Moment(
            title=body.title,
            content=body.content,
            is_published=False,
            user_id=user.id,
            last_edited_at=datetime.now(timezone.utc),
        )
        db.add(draft)

    await db.flush()
    return 构建动态草稿读取响应(draft)


async def 发布动态(
    db: AsyncSession,
    body: MomentCreate,
    user: User,
) -> MomentRead:
    """发布动态。"""
    now = datetime.now(timezone.utc)
    draft = await 获取草稿(db, user)
    if draft is not None:
        draft.title = body.title
        draft.content = body.content
        draft.is_published = True
        draft.published_at = now
        刷新动态最后编辑时间(draft, now=now)
        moment = draft
    else:
        moment = Moment(
            title=body.title,
            content=body.content,
            is_published=True,
            user_id=user.id,
            published_at=now,
            last_edited_at=now,
        )
        db.add(moment)
    await db.flush()
    await 同步动态Feed条目(db, moment)
    await db.flush()
    await 清除Feed首页缓存()

    result = await db.execute(动态查询().where(Moment.id == moment.id))
    return 构建动态读取响应(result.scalar_one())


async def 更新动态(
    db: AsyncSession,
    moment_id: str,
    body: MomentUpdate,
    user: User,
) -> MomentRead:
    """更新已发布动态。"""
    moment = await 获取动态或404(db, moment_id)
    确保动态写入权限(moment, user)
    if not moment.is_published:
        raise HTTPException(status_code=400, detail="草稿请通过草稿接口保存")

    changed = False
    if moment.title != body.title:
        moment.title = body.title
        changed = True
    if moment.content != body.content:
        moment.content = body.content
        changed = True

    if changed:
        now = datetime.now(timezone.utc)
        刷新动态最后编辑时间(moment, now=now)
        await 同步动态Feed条目(db, moment)
        await db.flush()
        await 清除Feed首页缓存()

    result = await db.execute(动态查询().where(Moment.id == moment.id))
    return 构建动态读取响应(result.scalar_one())


async def 列出我的动态(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: User,
    is_deleted: bool,
) -> PaginatedResponse:
    """获取当前用户已发布动态列表。"""
    query = 动态查询().where(
        Moment.user_id == user.id,
        Moment.is_deleted.is_(is_deleted),
    )
    if not is_deleted:
        query = query.where(Moment.is_published.is_(True)).order_by(Moment.published_at.desc())
    else:
        query = query.order_by(Moment.deleted_at.desc(), Moment.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[构建动态读取响应(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 获取动态或404(db: AsyncSession, moment_id: str) -> Moment:
    """获取单个动态。"""
    result = await db.execute(
        select(Moment).where(
            Moment.id == moment_id,
            Moment.is_deleted.is_(False),
        )
    )
    moment = result.scalar_one_or_none()
    if moment is None:
        raise HTTPException(status_code=404, detail="动态不存在")
    return moment


async def 获取已删动态或404(db: AsyncSession, moment_id: str) -> Moment:
    """获取回收站中的动态。"""
    result = await db.execute(
        select(Moment).where(
            Moment.id == moment_id,
            Moment.is_deleted.is_(True),
        )
    )
    moment = result.scalar_one_or_none()
    if moment is None:
        raise HTTPException(status_code=404, detail="动态不存在或未被删除")
    return moment


async def 列出动态图片存储键(db: AsyncSession, moment_id: UUID) -> list[str]:
    """获取动态关联的全部图片对象键。"""
    result = await db.execute(
        select(MomentImage.storage_key).where(MomentImage.moment_id == moment_id)
    )
    return list(result.scalars().all())


def 确保动态删除权限(moment: Moment, user: User) -> None:
    """校验动态删除权限。"""
    确保动态写入权限(moment, user)


async def 删除动态(db: AsyncSession, moment_id: str, user: User, *, permanent: bool) -> None:
    """删除动态。"""
    if permanent:
        moment = await 获取已删动态或404(db, moment_id)
        确保动态删除权限(moment, user)
        image_storage_keys = await 列出动态图片存储键(db, moment.id)
        await 删除Feed条目(db, FeedItemType.moment, moment.id)
        await db.delete(moment)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await 清除Feed首页缓存()
        尽力删除多个对象(image_storage_keys)
        return

    moment = await 获取动态或404(db, moment_id)
    确保动态删除权限(moment, user)
    应用动态删除状态(moment)
    await 删除Feed条目(db, FeedItemType.moment, moment.id)
    await db.flush()
    await 清除Feed首页缓存()


async def 恢复动态(db: AsyncSession, moment_id: str, user: User) -> MomentRead:
    """从回收站恢复动态。"""
    moment = await 获取已删动态或404(db, moment_id)
    确保动态删除权限(moment, user)
    恢复动态删除状态(moment)
    await 同步动态Feed条目(db, moment)
    await db.flush()
    await 清除Feed首页缓存()

    result = await db.execute(动态查询().where(Moment.id == moment.id))
    return 构建动态读取响应(result.scalar_one())


__all__ = [
    "构建动态公开读取",
    "应用动态删除状态",
    "删除动态",
    "确保动态删除权限",
    "获取草稿",
    "获取已删动态或404",
    "获取动态或404",
    "获取公开动态或404",
    "点赞动态",
    "列出动态图片存储键",
    "列出动态",
    "列出我的动态",
    "动态查询",
    "发布动态",
    "记录动态浏览",
    "恢复动态",
    "恢复动态删除状态",
    "保存草稿",
    "刷新动态最后编辑时间",
    "un点赞动态",
    "更新动态",
]
