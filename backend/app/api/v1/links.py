"""友链 CRUD 路由。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import Unix纪元时间, build_conditional_json_response
from app.api.deps import require_super_admin
from app.core.database import get_db
from app.models.link import Link, LinkStatus
from app.models.user import User
from app.schemas.link import LinkCreate, LinkExchangeRequest, LinkPublicRead, LinkRead, LinkUpdate
from app.schemas.shared import PaginatedResponse
from app.services.link_service import (
    approve_link as approve_link_service,
    create_link as create_link_service,
    delete_link as delete_link_service,
    exchange_link as exchange_link_service,
    get_link_or_404,
    list_links as list_links_service,
    list_public_links as list_public_links_service,
    reject_link as reject_link_service,
    update_link as update_link_service,
)

router = APIRouter(prefix="/links", tags=["links"])


@router.get("", response_model=PaginatedResponse)
async def list_links(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取管理端友链列表。

    Args:
        page: 页码
        page_size: 每页数量
        status: 友链状态筛选
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页友链数据
    """
    return await list_links_service(db, page=page, page_size=page_size, status=status)


@router.get("/public", response_model=list[LinkPublicRead])
async def list_public_links(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取公开友链列表。

    Args:
        db: 数据库会话

    Returns:
        list[LinkPublicRead]: 公开友链
    """
    payload = await list_public_links_service(db)
    last_modified_result = await db.execute(
        select(func.max(Link.updated_at)).where(Link.status == LinkStatus.approved)
    )
    last_modified = last_modified_result.scalar_one() or Unix纪元时间
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.get("/{link_id}", response_model=LinkRead)
async def get_link(
    link_id: str,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取友链详情。

    Args:
        link_id: 友链 ID
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        LinkRead: 友链详情
    """
    return await get_link_or_404(db, link_id)


@router.post("", response_model=LinkRead, status_code=status.HTTP_201_CREATED)
async def create_link(
    body: LinkCreate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    创建友链。

    Args:
        body: 创建请求体
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        LinkRead: 新建友链
    """
    return await create_link_service(db, body)


@router.patch("/{link_id}", response_model=LinkRead)
async def update_link(
    link_id: str,
    body: LinkUpdate,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新友链。

    Args:
        link_id: 友链 ID
        body: 更新请求体
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        LinkRead: 更新后的友链
    """
    return await update_link_service(db, link_id, body)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: str,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    删除友链。

    Args:
        link_id: 友链 ID
        _super_admin: 当前超级管理员
        db: 数据库会话
    """
    await delete_link_service(db, link_id)


@router.post("/exchange", response_model=dict)
async def exchange_link(
    body: LinkExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    自动交换友链。

    Args:
        body: 交换申请请求体
        db: 数据库会话

    Returns:
        dict: 自动审核结果与友链数据
    """
    return await exchange_link_service(db, body)


@router.post("/{link_id}/approve", response_model=LinkRead)
async def approve_link(
    link_id: str,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    通过友链申请。

    Args:
        link_id: 友链 ID
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        LinkRead: 审核后的友链
    """
    return await approve_link_service(db, link_id)


@router.post("/{link_id}/reject", response_model=LinkRead)
async def reject_link(
    link_id: str,
    _super_admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    拒绝友链申请。

    Args:
        link_id: 友链 ID
        _super_admin: 当前超级管理员
        db: 数据库会话

    Returns:
        LinkRead: 审核后的友链
    """
    return await reject_link_service(db, link_id)
