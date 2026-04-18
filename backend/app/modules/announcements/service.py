"""公告模块服务。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.announcements.models import Announcement
from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementPublicRead, AnnouncementRead, AnnouncementUpdate
from app.schemas.shared import PaginatedResponse


async def list_public_announcements(
    db: AsyncSession,
    *,
    limit: int,
) -> list[AnnouncementPublicRead]:
    """获取当前生效的公告列表。"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    announcements = result.scalars().all()
    return [AnnouncementPublicRead.model_validate(item) for item in announcements]


async def get_latest_public_announcement(db: AsyncSession) -> AnnouncementPublicRead | None:
    """获取最新的生效公告。"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(1)
    )
    announcement = result.scalar_one_or_none()
    return AnnouncementPublicRead.model_validate(announcement) if announcement is not None else None


async def list_announcements(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """获取公告分页列表。"""
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count()).select_from(Announcement))
    total = count_result.scalar() or 0
    result = await db.execute(
        select(Announcement)
        .order_by(desc(Announcement.created_at))
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


async def get_announcement_or_404(db: AsyncSession, announcement_id: UUID) -> Announcement:
    """获取单个公告。"""
    announcement = await db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    return announcement


async def create_announcement(db: AsyncSession, body: AnnouncementCreate, current_user: User) -> Announcement:
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


async def update_announcement(
    db: AsyncSession,
    announcement_id: UUID,
    body: AnnouncementUpdate,
) -> Announcement:
    """更新公告。"""
    announcement = await get_announcement_or_404(db, announcement_id)

    if body.title is not None:
        announcement.title = body.title
    if body.content is not None:
        announcement.content = body.content
    if body.is_active is not None:
        announcement.is_active = body.is_active

    await db.commit()
    await db.refresh(announcement)
    return announcement


async def delete_announcement(db: AsyncSession, announcement_id: UUID) -> None:
    """删除公告。"""
    announcement = await get_announcement_or_404(db, announcement_id)
    await db.delete(announcement)
    await db.commit()
