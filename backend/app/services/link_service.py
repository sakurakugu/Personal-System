"""友链领域服务。"""

from __future__ import annotations

import math
import re

import httpx
from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.link import Link, LinkStatus
from app.schemas.link import LinkCreate, LinkExchangeRequest, LinkPublicRead, LinkRead, LinkUpdate
from app.schemas.shared import PaginatedResponse


def parse_link_status(value: str) -> LinkStatus:
    """解析友链状态。"""
    try:
        return LinkStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的友链状态") from exc


def normalize_domain(url: str) -> str:
    """提取用于匹配的规范域名片段。"""
    normalized = url.lower().replace("https://", "").replace("http://", "").strip("/")
    if normalized.startswith("www."):
        return normalized.removeprefix("www.")
    return normalized


def contains_backlink(content: str, my_site_url: str) -> bool:
    """检查页面内容中是否包含本站链接。"""
    normalized_content = content.lower()
    my_domain = normalize_domain(my_site_url)
    patterns = [
        rf'href=["\']https?://[^"\']*{re.escape(my_domain)}[^"\']*["\']',
        rf'href=["\'][^"\']*{re.escape(my_domain)}[^"\']*["\']',
    ]
    return any(re.search(pattern, normalized_content) for pattern in patterns)


async def check_backlink(my_site_url: str, target_url: str) -> bool:
    """请求对方站点并检查是否已挂本站链接。"""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
                },
            )
            response.raise_for_status()
            return contains_backlink(response.text, my_site_url)
    except Exception:
        return False


async def get_link_or_404(db: AsyncSession, link_id: str) -> Link:
    """按 ID 获取友链。"""
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="友链不存在")
    return link


async def list_links(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None,
) -> PaginatedResponse:
    """获取管理端友链列表。"""
    query = select(Link)
    if status is not None:
        query = query.where(Link.status == parse_link_status(status))

    pending_first = case((Link.status == LinkStatus.pending, 0), else_=1)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(pending_first.asc(), Link.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(
        items=[LinkRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def list_public_links(db: AsyncSession) -> list[LinkPublicRead]:
    """获取公开友链。"""
    result = await db.execute(
        select(Link)
        .where(Link.status == LinkStatus.approved)
        .order_by(Link.created_at.desc())
    )
    items = result.scalars().all()
    return [LinkPublicRead.model_validate(item) for item in items]


async def create_link(db: AsyncSession, body: LinkCreate) -> Link:
    """创建友链。"""
    link = Link(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        status=LinkStatus.approved,
        is_auto_exchange=False,
        contact_email=body.contact_email,
        contact_name=body.contact_name,
    )
    db.add(link)
    await db.flush()
    return link


async def update_link(db: AsyncSession, link_id: str, body: LinkUpdate) -> Link:
    """更新友链。"""
    link = await get_link_or_404(db, link_id)
    data = body.model_dump(exclude_unset=True)
    status_value = data.pop("status", None)

    for key, value in data.items():
        setattr(link, key, value)

    if status_value is not None:
        link.status = parse_link_status(status_value)

    await db.flush()
    return link


async def delete_link(db: AsyncSession, link_id: str) -> None:
    """删除友链。"""
    link = await get_link_or_404(db, link_id)
    await db.delete(link)


async def exchange_link(db: AsyncSession, body: LinkExchangeRequest) -> dict:
    """自动交换友链。"""
    existing = await db.execute(select(Link.id).where(Link.url == body.url))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="该网站已申请过友链")

    site_url = settings.SITE_URL or body.my_site_url
    has_backlink = await check_backlink(site_url, body.my_site_url)
    link = Link(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        status=LinkStatus.approved if has_backlink else LinkStatus.pending,
        is_auto_exchange=True,
        contact_email=body.contact_email,
        contact_name=body.contact_name,
    )
    db.add(link)
    await db.flush()

    return {
        "message": "友链交换成功！已自动添加。"
        if has_backlink
        else "已提交友链申请，等待查看中。检测到您的网站尚未添加本站链接，添加后可自动显示（大概，还没测试）。",
        "auto_approved": has_backlink,
        "link": LinkRead.model_validate(link),
    }


async def approve_link(db: AsyncSession, link_id: str) -> Link:
    """通过友链申请。"""
    link = await get_link_or_404(db, link_id)
    link.status = LinkStatus.approved
    await db.flush()
    return link


async def reject_link(db: AsyncSession, link_id: str) -> Link:
    """拒绝友链申请。"""
    link = await get_link_or_404(db, link_id)
    link.status = LinkStatus.rejected
    await db.flush()
    return link
