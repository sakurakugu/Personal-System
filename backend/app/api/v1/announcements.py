"""公告管理路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_super_admin
from app.core.database import get_db
from app.models.models import Announcement, User
from app.schemas.schemas import (
    AnnouncementCreate,
    AnnouncementPublicRead,
    AnnouncementRead,
    AnnouncementUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/public", response_model=list[AnnouncementPublicRead])
async def get_public_announcements(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """获取当前生效的公告列表（公开接口）"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    announcements = result.scalars().all()
    return announcements


@router.get("/public/latest", response_model=AnnouncementPublicRead | None)
async def get_latest_announcement(db: AsyncSession = Depends(get_db)):
    """获取最新的生效公告（公开接口）"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active.is_(True))
        .order_by(desc(Announcement.created_at))
        .limit(1)
    )
    announcement = result.scalar_one_or_none()
    return announcement


@router.get("", response_model=PaginatedResponse)
async def list_announcements(
    page: int = 1,
    page_size: int = 10,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取公告列表（超级管理员）"""
    offset = (page - 1) * page_size

    # 获取总数（使用 COUNT 优化）
    count_result = await db.execute(select(func.count()).select_from(Announcement))
    total = count_result.scalar() or 0

    # 获取分页数据
    result = await db.execute(
        select(Announcement)
        .order_by(desc(Announcement.created_at))
        .offset(offset)
        .limit(page_size)
    )
    items = result.scalars().all()

    pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    # 转换为 Pydantic 模型列表
    announcement_list = [AnnouncementRead.model_validate(item) for item in items]

    return PaginatedResponse(
        items=announcement_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    body: AnnouncementCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建公告（超级管理员）"""
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


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement(
    announcement_id: UUID,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取单个公告详情（超级管理员）"""
    announcement = await db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    return announcement


@router.patch("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    announcement_id: UUID,
    body: AnnouncementUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新公告（超级管理员）"""
    announcement = await db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")

    if body.title is not None:
        announcement.title = body.title
    if body.content is not None:
        announcement.content = body.content
    if body.is_active is not None:
        announcement.is_active = body.is_active

    await db.commit()
    await db.refresh(announcement)
    return announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除公告（超级管理员）"""
    announcement = await db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")

    await db.delete(announcement)
    await db.commit()
    return None
