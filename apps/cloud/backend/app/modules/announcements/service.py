"""公告模块服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.announcements.models import Announcement
from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementPublicRead, AnnouncementRead, AnnouncementUpdate
from app.shared.kernel.pagination import PaginatedResponse


async def 列出公开公告(
    db: AsyncSession,
    *,
    limit: int,
) -> list[AnnouncementPublicRead]:
    """获取当前生效的公告列表。"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True), Announcement.is_deleted.is_(False))
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    announcements = result.scalars().all()
    return [AnnouncementPublicRead.model_validate(item) for item in announcements]


async def 获取最新公开公告(db: AsyncSession) -> AnnouncementPublicRead | None:
    """获取最新的生效公告。"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True), Announcement.is_deleted.is_(False))
        .order_by(desc(Announcement.created_at))
        .limit(1)
    )
    announcement = result.scalar_one_or_none()
    return AnnouncementPublicRead.model_validate(announcement) if announcement is not None else None


async def 列出公告(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    is_deleted: bool = False,
) -> PaginatedResponse:
    """获取公告分页列表。"""
    offset = (page - 1) * page_size
    query = select(Announcement).where(Announcement.is_deleted.is_(is_deleted))
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    primary_order_column = desc(Announcement.deleted_at) if is_deleted else desc(Announcement.created_at)
    result = await db.execute(
        query.order_by(primary_order_column)
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[AnnouncementRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


async def 获取公告或404(db: AsyncSession, announcement_id: UUID) -> Announcement:
    """获取单个公告。"""
    result = await db.execute(
        select(Announcement).where(
            Announcement.id == announcement_id,
            Announcement.is_deleted.is_(False),
        )
    )
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    return announcement


async def 获取已删公告或404(db: AsyncSession, announcement_id: UUID) -> Announcement:
    """获取回收站中的公告。"""
    result = await db.execute(
        select(Announcement).where(
            Announcement.id == announcement_id,
            Announcement.is_deleted.is_(True),
        )
    )
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在或未被删除")
    return announcement


def 应用公告删除状态(announcement: Announcement, *, now: datetime | None = None) -> None:
    """将公告标记为已删除。"""
    announcement.is_deleted = True
    announcement.deleted_at = now or datetime.now(timezone.utc)


def 恢复公告删除状态(announcement: Announcement) -> None:
    """恢复公告的删除状态。"""
    announcement.is_deleted = False
    announcement.deleted_at = None


async def 创建公告(db: AsyncSession, body: AnnouncementCreate, current_user: 用户) -> Announcement:
    """创建公告。"""
    announcement = Announcement(
        title=body.title,
        content=body.content,
        is_active=body.is_active,
        created_by=current_user.id,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return announcement


async def 更新公告(
    db: AsyncSession,
    announcement_id: UUID,
    body: AnnouncementUpdate,
) -> Announcement:
    """更新公告。"""
    announcement = await 获取公告或404(db, announcement_id)

    if body.title is not None:
        announcement.title = body.title
    if body.content is not None:
        announcement.content = body.content
    if body.is_active is not None:
        announcement.is_active = body.is_active

    await db.commit()
    await db.refresh(announcement)
    return announcement


async def 删除公告(db: AsyncSession, announcement_id: UUID, *, permanent: bool) -> None:
    """删除公告。"""
    if permanent:
        announcement = await 获取已删公告或404(db, announcement_id)
        await db.delete(announcement)
        await db.commit()
        return

    announcement = await 获取公告或404(db, announcement_id)
    应用公告删除状态(announcement)
    await db.commit()


async def 恢复公告(db: AsyncSession, announcement_id: UUID) -> Announcement:
    """从回收站恢复公告。"""
    announcement = await 获取已删公告或404(db, announcement_id)
    恢复公告删除状态(announcement)
    await db.commit()
    await db.refresh(announcement)
    return announcement
