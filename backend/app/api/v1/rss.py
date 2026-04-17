"""RSS 订阅接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.database import get_db
from app.services.feed_service import list_feed_items
from app.services.rss_service import build_rss_xml

router = APIRouter(prefix="/rss.xml", tags=["rss"])


@router.get("", response_class=Response)
async def rss_feed(db: AsyncSession = Depends(get_db)) -> Response:
    """获取未登录动态流的 RSS 订阅（仅公开文章）。"""
    paginated = await list_feed_items(
        db,
        page=1,
        page_size=20,
        current_user=None,
        category=None,
        tag=None,
        search=None,
        include_own_private=False,
    )
    xml = build_rss_xml(paginated.items)
    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")
