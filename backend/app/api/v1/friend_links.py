"""友链路由兼容入口。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import Unix纪元时间, build_conditional_json_response
from app.models.friend_link import FriendLink, FriendLinkStatus
from app.modules.friend_links.api import router
from app.modules.friend_links.schemas import FriendLinkPublicRead
from app.modules.friend_links.service import list_public_friend_links as list_public_friend_links_service


async def list_public_friend_links(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession | None = None,
):
    """获取公开友链列表。"""
    assert db is not None
    payload = await list_public_friend_links_service(db)
    last_modified_result = await db.execute(
        select(func.max(FriendLink.updated_at)).where(FriendLink.status == FriendLinkStatus.approved)
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


__all__ = ["FriendLinkPublicRead", "list_public_friend_links", "list_public_friend_links_service", "router"]
