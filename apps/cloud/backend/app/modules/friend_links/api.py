"""友链模块路由。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import UTC时间戳起点, 构建条件JSON响应
from app.modules.users.models import User
from app.modules.friend_links.models import FriendLink, FriendLinkStatus
from app.modules.friend_links.schemas import (
    FriendLinkCreate,
    FriendLinkExchangeRequest,
    FriendLinkPublicRead,
    FriendLinkRead,
    FriendLinkUpdate,
)
from app.modules.friend_links.service import (
    批准友链 as 批准友链_service,
    创建友链 as 创建友链_service,
    删除友链 as 删除友链_service,
    交换友链 as 交换友链_service,
    获取友链或404,
    列出友链分类 as 列出友链分类_service,
    列出友链 as 列出友链_service,
    列出公开友链 as 列出公开友链_service,
    拒绝友链 as 拒绝友链_service,
    更新友链 as 更新友链_service,
)
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.auth.deps import 要求超级管理员权限
from app.shared.db.session import get_db

router = APIRouter(prefix="/friend-links", tags=["friend-links"])


@router.get("", response_model=PaginatedResponse)
async def 列出友链(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取管理端友链列表。"""
    return await 列出友链_service(db, page=page, page_size=page_size, status=status)


@router.get("/categories", response_model=list[str])
async def 列出友链分类(
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取已有的友链分类列表。"""
    return await 列出友链分类_service(db)


@router.get("/public", response_model=list[FriendLinkPublicRead])
async def 列出公开友链(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取公开友链列表。"""
    payload = await 列出公开友链_service(db)
    last_modified_result = await db.execute(
        select(func.max(FriendLink.updated_at)).where(FriendLink.status == FriendLinkStatus.approved)
    )
    last_modified = last_modified_result.scalar_one() or UTC时间戳起点
    return 构建条件JSON响应(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("/{friend_link_id}", response_model=FriendLinkRead)
async def 获取友链(
    friend_link_id: str,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """获取友链详情。"""
    return await 获取友链或404(db, friend_link_id)


@router.post("", response_model=FriendLinkRead, status_code=status.HTTP_201_CREATED)
async def 创建友链(
    body: FriendLinkCreate,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """创建友链。"""
    return await 创建友链_service(db, body)


@router.patch("/{friend_link_id}", response_model=FriendLinkRead)
async def 更新友链(
    friend_link_id: str,
    body: FriendLinkUpdate,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """更新友链。"""
    return await 更新友链_service(db, friend_link_id, body)


@router.delete("/{friend_link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除友链(
    friend_link_id: str,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """删除友链。"""
    await 删除友链_service(db, friend_link_id)


@router.post("/exchange", response_model=dict)
async def 交换友链(
    body: FriendLinkExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """自动交换友链。"""
    return await 交换友链_service(db, body)


@router.post("/{friend_link_id}/approve", response_model=FriendLinkRead)
async def 批准友链(
    friend_link_id: str,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """通过友链申请。"""
    return await 批准友链_service(db, friend_link_id)


@router.post("/{friend_link_id}/reject", response_model=FriendLinkRead)
async def 拒绝友链(
    friend_link_id: str,
    _super_admin: User = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
):
    """拒绝友链申请。"""
    return await 拒绝友链_service(db, friend_link_id)
