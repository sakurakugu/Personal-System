"""首页 Feed 流接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.shared import PaginatedResponse
from app.services.feed_service import list_feed_items

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=PaginatedResponse)
async def list_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    include_own_private: bool = Query(False, description="是否额外包含当前用户自己的私有文章"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取首页统一时间流。"""
    return await list_feed_items(
        db,
        page=page,
        page_size=page_size,
        current_user=current_user,
        category=category,
        tag=tag,
        search=search,
        include_own_private=include_own_private,
    )
