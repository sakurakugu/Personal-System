"""公告管理路由。

此模块提供公告的 CRUD 操作，包括：
- 公开接口：获取当前生效的公告列表
- 管理接口：创建、更新、删除公告（仅超级管理员）
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_super_admin
from app.core.database import get_db
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementPublicRead,
    AnnouncementRead,
    AnnouncementUpdate,
)
from app.schemas.shared import (
    PaginatedResponse,
)

# 创建路由器，前缀为 /announcements，标签为 announcements
router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/public", response_model=list[AnnouncementPublicRead])
async def get_public_announcements(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前生效的公告列表（公开接口）。

    返回 is_active=True 的公告，按创建时间倒序排列。

    Args:
        limit: 返回的最大数量，默认 10 条
        db: 数据库会话

    Returns:
        list[AnnouncementPublicRead]: 公告列表
    """
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
    """
    获取最新的生效公告（公开接口）。

    Args:
        db: 数据库会话

    Returns:
        AnnouncementPublicRead | None: 最新公告或 None
    """
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
    """
    获取公告列表（超级管理员）。

    返回所有公告（包括已禁用的），支持分页。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量
        _super_admin: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的公告列表
    """
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
    """
    创建公告（超级管理员）。

    Args:
        body: 公告创建数据
        current_user: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        AnnouncementRead: 创建的公告
    """
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
    """
    获取单个公告详情（超级管理员）。

    Args:
        announcement_id: 公告 ID
        _super_admin: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        AnnouncementRead: 公告详情

    Raises:
        HTTPException: 404 - 公告不存在
    """
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
    """
    更新公告（超级管理员）。

    Args:
        announcement_id: 公告 ID
        body: 公告更新数据
        _super_admin: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        AnnouncementRead: 更新后的公告

    Raises:
        HTTPException: 404 - 公告不存在
    """
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
    """
    删除公告（超级管理员）。

    Args:
        announcement_id: 公告 ID
        _super_admin: 当前超级管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 公告不存在
    """
    announcement = await db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")

    await db.delete(announcement)
    await db.commit()
    return None
