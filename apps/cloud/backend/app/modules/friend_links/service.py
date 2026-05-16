"""友链领域服务。"""

from __future__ import annotations

import math
import re

import httpx
from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.friend_links.models import FriendLink, FriendLinkStatus
from app.modules.friend_links.schemas import (
    FriendLinkCreate,
    FriendLinkExchangeRequest,
    FriendLinkPublicRead,
    FriendLinkRead,
    FriendLinkUpdate,
)
from app.shared.kernel.pagination import PaginatedResponse


def 解析友链状态(value: str) -> FriendLinkStatus:
    """解析友链状态。"""
    try:
        return FriendLinkStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的友链状态") from exc


def 规范化域名(url: str) -> str:
    """提取用于匹配的规范域名片段。"""
    normalized = url.lower().replace("https://", "").replace("http://", "").strip("/")
    if normalized.startswith("www."):
        return normalized.removeprefix("www.")
    return normalized


def 包含回链(content: str, my_site_url: str) -> bool:
    """检查页面内容中是否包含本站链接。"""
    normalized_content = content.lower()
    my_domain = 规范化域名(my_site_url)
    patterns = [
        rf'href=["\']https?://[^"\']*{re.escape(my_domain)}[^"\']*["\']',
        rf'href=["\'][^"\']*{re.escape(my_domain)}[^"\']*["\']',
    ]
    return any(re.search(pattern, normalized_content) for pattern in patterns)


async def 检查回链(my_site_url: str, target_url: str) -> bool:
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
            return 包含回链(response.text, my_site_url)
    except Exception:
        return False


async def 获取友链或404(db: AsyncSession, friend_link_id: str) -> FriendLink:
    """按 ID 获取友链。"""
    result = await db.execute(select(FriendLink).where(FriendLink.id == friend_link_id))
    friend_link = result.scalar_one_or_none()
    if friend_link is None:
        raise HTTPException(status_code=404, detail="友链不存在")
    return friend_link


async def 列出友链(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None,
) -> PaginatedResponse:
    """获取管理端友链列表。"""
    query = select(FriendLink)
    if status is not None:
        query = query.where(FriendLink.status == 解析友链状态(status))

    pending_first = case((FriendLink.status == FriendLinkStatus.pending, 0), else_=1)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(pending_first.asc(), FriendLink.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(
        items=[FriendLinkRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 列出友链分类(db: AsyncSession) -> list[str]:
    """获取已有的友链分类列表（去重、非空、按字母排序）。"""
    result = await db.execute(
        select(FriendLink.category)
        .where(FriendLink.category.isnot(None))
        .where(FriendLink.category != "")
        .distinct()
        .order_by(FriendLink.category)
    )
    return [row[0] for row in result.all()]


async def 列出公开友链(db: AsyncSession) -> list[FriendLinkPublicRead]:
    """获取公开友链。"""
    result = await db.execute(
        select(FriendLink)
        .where(FriendLink.status == FriendLinkStatus.approved)
        .order_by(FriendLink.created_at.desc())
    )
    items = result.scalars().all()
    return [FriendLinkPublicRead.model_validate(item) for item in items]


async def 创建友链(db: AsyncSession, body: FriendLinkCreate) -> FriendLink:
    """创建友链。"""
    friend_link = FriendLink(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        category=body.category,
        status=FriendLinkStatus.approved,
        is_auto_exchange=False,
        contact_email=body.contact_email,
        contact_name=body.contact_name,
    )
    db.add(friend_link)
    await db.flush()
    return friend_link


async def 更新友链(db: AsyncSession, friend_link_id: str, body: FriendLinkUpdate) -> FriendLink:
    """更新友链。"""
    friend_link = await 获取友链或404(db, friend_link_id)
    data = body.model_dump(exclude_unset=True)
    status_value = data.pop("status", None)

    for key, value in data.items():
        setattr(friend_link, key, value)

    if status_value is not None:
        friend_link.status = 解析友链状态(status_value)

    await db.flush()
    return friend_link


async def 删除友链(db: AsyncSession, friend_link_id: str) -> None:
    """删除友链。"""
    friend_link = await 获取友链或404(db, friend_link_id)
    await db.delete(friend_link)


async def 交换友链(db: AsyncSession, body: FriendLinkExchangeRequest) -> dict:
    """自动交换友链。"""
    existing = await db.execute(select(FriendLink.id).where(FriendLink.url == body.url))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="该网站已申请过友链")

    site_url = settings.SITE_URL or body.my_site_url
    has_backlink = await 检查回链(site_url, body.my_site_url)
    friend_link = FriendLink(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        category=body.category,
        status=FriendLinkStatus.approved if has_backlink else FriendLinkStatus.pending,
        is_auto_exchange=True,
        contact_email=body.contact_email,
        contact_name=body.contact_name,
    )
    db.add(friend_link)
    await db.flush()

    return {
        "message": "友链交换成功！已自动添加。"
        if has_backlink
        else "已提交友链申请，等待查看中。检测到您的网站尚未添加本站链接，添加后可自动显示（大概，还没测试）。",
        "auto_approved": has_backlink,
        "link": FriendLinkRead.model_validate(friend_link),
    }


async def 批准友链(db: AsyncSession, friend_link_id: str) -> FriendLink:
    """通过友链申请。"""
    friend_link = await 获取友链或404(db, friend_link_id)
    friend_link.status = FriendLinkStatus.approved
    await db.flush()
    return friend_link


async def 拒绝友链(db: AsyncSession, friend_link_id: str) -> FriendLink:
    """拒绝友链申请。"""
    friend_link = await 获取友链或404(db, friend_link_id)
    friend_link.status = FriendLinkStatus.rejected
    await db.flush()
    return friend_link
