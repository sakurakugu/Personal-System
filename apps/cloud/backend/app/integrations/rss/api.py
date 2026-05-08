"""RSS 订阅接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.modules.feed.service import 列出Feed条目
from app.integrations.rss.service import 构建RSS_XML
from app.shared.db.session import get_db

router = APIRouter(prefix="/rss.xml", tags=["rss"])


@router.get("", response_class=Response)
async def rss_feed(db: AsyncSession = Depends(get_db)) -> Response:
    """获取未登录动态流的 RSS 订阅（仅公开文章）。"""
    paginated = await 列出Feed条目(
        db,
        page=1,
        page_size=20,
        current_user=None,
        category=None,
        tag=None,
        search=None,
        include_own_private=False,
    )
    xml = 构建RSS_XML(paginated.items)
    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")
