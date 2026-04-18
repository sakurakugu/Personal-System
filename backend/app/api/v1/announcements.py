"""公告路由兼容入口。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Header
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import Unix纪元时间, build_conditional_json_response
from app.models.announcement import Announcement
from app.modules.announcements.api import router
from app.modules.announcements.schemas import AnnouncementPublicRead


async def get_public_announcements(
    limit: int = 10,
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession | None = None,
):
    """获取当前生效的公告列表。"""
    assert db is not None
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    announcements = result.scalars().all()
    payload = [AnnouncementPublicRead.model_validate(item) for item in announcements]
    last_modified = max((item.updated_at for item in announcements), default=Unix纪元时间)
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


async def get_latest_announcement(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession | None = None,
):
    """获取最新的生效公告。"""
    assert db is not None
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(1)
    )
    announcement = result.scalar_one_or_none()
    payload = AnnouncementPublicRead.model_validate(announcement) if announcement is not None else None
    last_modified = announcement.updated_at if announcement is not None else Unix纪元时间
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


__all__ = ["AnnouncementPublicRead", "get_latest_announcement", "get_public_announcements", "router"]
