"""公告模块路由。"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import UTC时间戳起点, 构建条件JSON响应
from app.modules.users.models import User
from app.modules.announcements.models import Announcement
from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementPublicRead, AnnouncementRead, AnnouncementUpdate
from app.modules.announcements.service import (
    创建公告 as 创建公告_service,
    删除公告 as 删除公告_service,
    获取公告或404,
    获取最新公开公告,
    列出公告 as 列出公告_service,
    列出公开公告 as 列出公开公告_service,
    更新公告 as 更新公告_service,
)
from app.shared.auth.deps import 要求超级管理员权限
from app.shared.db.session import get_db

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/public", response_model=list[AnnouncementPublicRead])
async def 获取公开公告(
    limit: int = 10,
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取当前生效的公告列表。"""
    payload = await 列出公开公告_service(db, limit=limit)
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    announcements = result.scalars().all()
    last_modified = max((item.updated_at for item in announcements), default=UTC时间戳起点)
    return 构建条件JSON响应(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("/public/latest", response_model=AnnouncementPublicRead | None)
async def 获取最新公告(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取最新的生效公告。"""
    payload = await 获取最新公开公告(db)
    last_modified = payload.created_at if payload is not None else UTC时间戳起点
    if payload is not None:
        announcement = await db.execute(
            select(Announcement)
            .where(Announcement.is_active.is_(True))
            .order_by(desc(Announcement.created_at))
            .limit(1)
        )
        raw = announcement.scalar_one_or_none()
        last_modified = raw.updated_at if raw is not None else UTC时间戳起点
    return 构建条件JSON响应(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("", response_model=object)
async def 列出公告(
    page: int = 1,
    page_size: int = 10,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取公告列表。"""
    return await 列出公告_service(db, page=page, page_size=page_size)


@router.post("", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def 创建公告(
    body: AnnouncementCreate,
    current_user: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """创建公告。"""
    return await 创建公告_service(db, body, current_user)


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def 获取公告(
    announcement_id: UUID,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取单个公告详情。"""
    return await 获取公告或404(db, announcement_id)


@router.patch("/{announcement_id}", response_model=AnnouncementRead)
async def 更新公告(
    announcement_id: UUID,
    body: AnnouncementUpdate,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """更新公告。"""
    return await 更新公告_service(db, announcement_id, body)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除公告(
    announcement_id: UUID,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """删除公告。"""
    await 删除公告_service(db, announcement_id)
