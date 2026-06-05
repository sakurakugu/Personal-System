"""友链领域服务。"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.friend_links.models import 友链, 友链状态
from app.modules.friend_links.schemas import (
    友链创建,
    友链交换请求,
    友链公开信息,
    友链信息,
    友链更新,
)
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.kernel.soft_delete import 可软删除对象


def 解析友链状态(value: str) -> 友链状态:
    """解析友链状态。"""
    try:
        return 友链状态(value)
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
                    "用户-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
                },
            )
            response.raise_for_status()
            return 包含回链(response.text, my_site_url)
    except Exception:
        return False


async def 获取友链或404(db: AsyncSession, friend_link_id: str) -> 友链:
    """按 ID 获取友链。"""
    result = await db.execute(select(友链).where(友链.id == friend_link_id, 友链.is_deleted.is_(False)))
    friend_link = result.scalar_one_or_none()
    if friend_link is None:
        raise HTTPException(status_code=404, detail="友链不存在")
    return friend_link


async def 获取已删友链或404(db: AsyncSession, friend_link_id: str) -> 友链:
    """按 ID 获取回收站中的友链。"""
    result = await db.execute(select(友链).where(友链.id == friend_link_id, 友链.is_deleted.is_(True)))
    friend_link = result.scalar_one_or_none()
    if friend_link is None:
        raise HTTPException(status_code=404, detail="友链不存在或未被删除")
    return friend_link


def 应用友链删除状态(friend_link: 可软删除对象, *, now: datetime | None = None) -> None:
    """将友链标记为已删除。"""
    friend_link.is_deleted = True
    friend_link.deleted_at = now or datetime.now(timezone.utc)


def 恢复友链删除状态(friend_link: 可软删除对象) -> None:
    """恢复友链的删除状态。"""
    friend_link.is_deleted = False
    friend_link.deleted_at = None


async def 列出友链(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: str | None,
    is_deleted: bool = False,
) -> PaginatedResponse:
    """获取管理端友链列表。"""
    query = select(友链).where(友链.is_deleted.is_(is_deleted))
    if status is not None:
        query = query.where(友链.status == 解析友链状态(status))

    pending_first = case((友链.status == 友链状态.pending, 0), else_=1)
    primary_order_column = 友链.deleted_at.desc() if is_deleted else 友链.created_at.desc()
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(pending_first.asc(), primary_order_column).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(
        items=[友链信息.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 列出友链分类(db: AsyncSession) -> list[str]:
    """获取已有的友链分类列表（去重、非空、按字母排序）。"""
    result = await db.execute(
        select(友链.category)
        .where(友链.category.isnot(None))
        .where(友链.is_deleted.is_(False))
        .where(友链.category != "")
        .distinct()
        .order_by(友链.category)
    )
    return [row[0] for row in result.all()]


async def 列出公开友链(db: AsyncSession) -> list[友链公开信息]:
    """获取公开友链。"""
    result = await db.execute(
        select(友链)
        .where(友链.status == 友链状态.approved, 友链.is_deleted.is_(False))
        .order_by(友链.created_at.desc())
    )
    items = result.scalars().all()
    return [友链公开信息.model_validate(item) for item in items]


async def 创建友链(db: AsyncSession, body: 友链创建) -> 友链:
    """创建友链。"""
    friend_link = 友链(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        category=body.category,
        status=友链状态.approved,
        is_auto_exchange=False,
        contact_email=body.contact_email,
        contact_name=body.contact_name,
    )
    db.add(friend_link)
    await db.flush()
    return friend_link


async def 更新友链(db: AsyncSession, friend_link_id: str, body: 友链更新) -> 友链:
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


async def 删除友链(db: AsyncSession, friend_link_id: str, *, permanent: bool) -> None:
    """删除友链。"""
    if permanent:
        friend_link = await 获取已删友链或404(db, friend_link_id)
        await db.delete(friend_link)
        return

    friend_link = await 获取友链或404(db, friend_link_id)
    应用友链删除状态(friend_link)
    await db.flush()


async def 交换友链(db: AsyncSession, body: 友链交换请求) -> dict:
    """自动交换友链。"""
    existing = await db.execute(select(友链.id).where(友链.url == body.url, 友链.is_deleted.is_(False)))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="该网站已申请过友链")

    site_url = settings.SITE_URL or body.my_site_url
    has_backlink = await 检查回链(site_url, body.my_site_url)
    friend_link = 友链(
        name=body.name,
        url=body.url,
        description=body.description,
        logo_url=body.logo_url,
        category=body.category,
        status=友链状态.approved if has_backlink else 友链状态.pending,
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
        "link": 友链信息.model_validate(friend_link),
    }


async def 批准友链(db: AsyncSession, friend_link_id: str) -> 友链:
    """通过友链申请。"""
    friend_link = await 获取友链或404(db, friend_link_id)
    friend_link.status = 友链状态.approved
    await db.flush()
    return friend_link


async def 恢复友链(db: AsyncSession, friend_link_id: str) -> 友链:
    """从回收站恢复友链。"""
    friend_link = await 获取已删友链或404(db, friend_link_id)
    existing = await db.execute(select(友链.id).where(友链.url == friend_link.url, 友链.is_deleted.is_(False)))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="同 URL 的友链已存在，无法恢复")
    恢复友链删除状态(friend_link)
    await db.flush()
    return friend_link


async def 拒绝友链(db: AsyncSession, friend_link_id: str) -> 友链:
    """拒绝友链申请。"""
    friend_link = await 获取友链或404(db, friend_link_id)
    friend_link.status = 友链状态.rejected
    await db.flush()
    return friend_link
