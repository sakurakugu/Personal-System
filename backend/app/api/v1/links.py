"""友链 CRUD 路由。

此模块提供友情链接管理接口，包括：
- 友链列表查询（管理员和公开接口）
- 创建、更新、删除友链
- 友链交换（自动检测对方是否已添加本站链接）
- 友链审核（通过/拒绝）
"""

from __future__ import annotations

import math
import re


import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import Link, LinkStatus, User
from app.schemas.schemas import (
    LinkCreate,
    LinkExchangeRequest,
    LinkPublicRead,
    LinkRead,
    LinkUpdate,
    PaginatedResponse,
)

# 创建路由器，前缀为 /links，标签为 links
router = APIRouter(prefix="/links", tags=["links"])


@router.get("", response_model=PaginatedResponse)
async def list_links(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取友链列表（管理员）。

    支持按状态筛选，支持分页。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量，范围 1-100
        status: 友链状态筛选（approved、pending、rejected），可选
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的友链列表
    """
    q = select(Link)
    if status:
        q = q.where(Link.status == status)
    
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Link.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[LinkRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/public", response_model=list[LinkPublicRead])
async def list_public_links(
    db: AsyncSession = Depends(get_db),
):
    """
    获取公开的友链列表。

    只返回已通过审核的友链，按创建时间倒序排列。

    Args:
        db: 数据库会话

    Returns:
        list[LinkPublicRead]: 公开的友链列表
    """
    result = await db.execute(
        select(Link)
        .where(Link.status == LinkStatus.approved)
        .order_by(Link.created_at.desc())
    )
    items = result.scalars().all()
    return [LinkPublicRead.model_validate(item) for item in items]


@router.get("/{link_id}", response_model=LinkRead)
async def get_link(
    link_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取友链详情。

    Args:
        link_id: 友链 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        LinkRead: 友链详情

    Raises:
        HTTPException: 404 - 友链不存在
    """
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")
    return link


@router.post("", response_model=LinkRead, status_code=status.HTTP_201_CREATED)
async def create_link(
    body: LinkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建友链（管理员）。

    管理员直接创建的友链状态为已通过。

    Args:
        body: 友链创建数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        LinkRead: 创建的友链
    """
    link = Link(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        status=LinkStatus.approved,  # 管理员直接创建为已通过
        is_auto_exchange=False,
        contact_email=body.contact_email,
        contact_name=body.contact_name,
    )
    db.add(link)
    await db.flush()
    return link


@router.patch("/{link_id}", response_model=LinkRead)
async def update_link(
    link_id: str,
    body: LinkUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新友链。

    Args:
        link_id: 友链 ID
        body: 友链更新数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        LinkRead: 更新后的友链

    Raises:
        HTTPException: 404 - 友链不存在
    """
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")
    
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(link, k, v)
    
    await db.flush()
    return link


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除友链。

    Args:
        link_id: 友链 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 友链不存在
    """
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")
    await db.delete(link)


async def check_backlink(my_site_url: str, target_url: str) -> bool:
    """
    检查对方网站是否包含本站的链接。

    通过 HTTP 请求获取对方网站内容，检查是否包含本站链接。

    Args:
        my_site_url: 本站 URL
        target_url: 对方网站 URL

    Returns:
        bool: 是否检测到本站链接
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
            }
            response = await client.get(target_url, headers=headers)
            response.raise_for_status()
            
            content = response.text.lower()
            # 提取域名进行模糊匹配
            my_domain = my_site_url.lower().replace("https://", "").replace("http://", "").strip("/")
            
            # 检查是否包含本站链接
            patterns = [
                rf'href=["\']https?://[^"\']*{re.escape(my_domain)}[^"\']*["\']',
                rf'href=["\'][^"\']*{re.escape(my_domain)}[^"\']*["\']',
            ]
            
            for pattern in patterns:
                if re.search(pattern, content):
                    return True
            
            return False
    except Exception:
        return False


@router.post("/exchange", response_model=dict)
async def exchange_link(
    body: LinkExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    自动交换友链。

    流程：
    1. 检查对方网站是否已添加本站的链接
    2. 如果已添加，自动通过审核
    3. 如果没有添加，创建待审核的友链申请

    Args:
        body: 友链交换请求数据
        db: 数据库会话

    Returns:
        dict: 包含消息、是否自动通过、友链信息

    Raises:
        HTTPException: 400 - 该网站已申请过友链
    """
    # 检查 URL 是否已存在
    existing = await db.execute(select(Link).where(Link.url == body.url))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该网站已申请过友链")
    
    # 获取本站 URL（从配置或请求头）
    my_site_url = settings.SITE_URL or body.my_site_url
    
    # 检查对方网站是否有本站链接
    has_backlink = await check_backlink(my_site_url, body.my_site_url)
    
    if has_backlink:
        # 自动通过
        link = Link(
            name=body.name,
            url=body.url,
            description=body.description,
            logo_url=body.logo_url,
            status=LinkStatus.approved,
            is_auto_exchange=True,
            contact_email=body.contact_email,
            contact_name=body.contact_name,
        )
        db.add(link)
        await db.flush()
        return {
            "message": "友链交换成功！已自动添加。",
            "auto_approved": True,
            "link": LinkRead.model_validate(link),
        }
    else:
        # 创建待审核的友链
        link = Link(
            name=body.name,
            url=body.url,
            description=body.description,
            logo_url=body.logo_url,
            status=LinkStatus.pending,
            is_auto_exchange=True,
            contact_email=body.contact_email,
            contact_name=body.contact_name,
        )
        db.add(link)
        await db.flush()
        return {
            "message": "已提交友链申请，等待查看中。检测到您的网站尚未添加本站链接，添加后可自动显示（大概，还没测试）。",
            "auto_approved": False,
            "link": LinkRead.model_validate(link),
        }


@router.post("/{link_id}/approve", response_model=LinkRead)
async def approve_link(
    link_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    审核通过友链。

    Args:
        link_id: 友链 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        LinkRead: 审核通过的友链

    Raises:
        HTTPException: 404 - 友链不存在
    """
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")
    
    link.status = LinkStatus.approved
    await db.flush()
    return link


@router.post("/{link_id}/reject", response_model=LinkRead)
async def reject_link(
    link_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    拒绝友链。

    Args:
        link_id: 友链 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        LinkRead: 被拒绝的友链

    Raises:
        HTTPException: 404 - 友链不存在
    """
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")
    
    link.status = LinkStatus.rejected
    await db.flush()
    return link
