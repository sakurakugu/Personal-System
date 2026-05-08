"""首页 Feed 流接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feed.service import 列出Feed条目
from app.modules.users.models import User
from app.shared.engagement import 获取访客ID
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.auth.deps import 获取当前用户可选
from app.shared.db.session import get_db

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=PaginatedResponse)
async def list_feed(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    include_own_private: bool = Query(False, description="是否额外包含当前用户自己的私有文章"),
    current_user: User | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """获取首页统一时间流。"""
    return await 列出Feed条目(
        db,
        page=page,
        page_size=page_size,
        current_user=current_user,
        category=category,
        tag=tag,
        search=search,
        include_own_private=include_own_private,
        visitor_id=获取访客ID(request),
    )
