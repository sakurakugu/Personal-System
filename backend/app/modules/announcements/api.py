"""公告模块路由。"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import Unix纪元时间, build_conditional_json_response
from app.models.user import User
from app.modules.announcements.models import Announcement
from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementPublicRead, AnnouncementRead, AnnouncementUpdate
from app.modules.announcements.service import (
    create_announcement as create_announcement_service,
    delete_announcement as delete_announcement_service,
    get_announcement_or_404,
    get_latest_public_announcement,
    list_announcements as list_announcements_service,
    list_public_announcements as list_public_announcements_service,
    update_announcement as update_announcement_service,
)
from app.shared.auth.deps import require_super_admin
from app.shared.db.session import get_db

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/public", response_model=list[AnnouncementPublicRead])
async def get_public_announcements(
    limit: int = 10,
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取当前生效的公告列表。"""
    payload = await list_public_announcements_service(db, limit=limit)
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    announcements = result.scalars().all()
    last_modified = max((item.updated_at for item in announcements), default=Unix纪元时间)
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("/public/latest", response_model=AnnouncementPublicRead | None)
async def get_latest_announcement(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取最新的生效公告。"""
    payload = await get_latest_public_announcement(db)
    last_modified = payload.created_at if payload is not None else Unix纪元时间
    if payload is not None:
        announcement = await db.execute(
            select(Announcement)
            .where(Announcement.is_active.is_(True))
            .order_by(desc(Announcement.created_at))
            .limit(1)
        )
        raw = announcement.scalar_one_or_none()
        last_modified = raw.updated_at if raw is not None else Unix纪元时间
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("", response_model=object)
async def list_announcements(
    page: int = 1,
    page_size: int = 10,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取公告列表。"""
    return await list_announcements_service(db, page=page, page_size=page_size)


@router.post("", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    body: AnnouncementCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建公告。"""
    return await create_announcement_service(db, body, current_user)


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement(
    announcement_id: UUID,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取单个公告详情。"""
    return await get_announcement_or_404(db, announcement_id)


@router.patch("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    announcement_id: UUID,
    body: AnnouncementUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新公告。"""
    return await update_announcement_service(db, announcement_id, body)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除公告。"""
    await delete_announcement_service(db, announcement_id)
