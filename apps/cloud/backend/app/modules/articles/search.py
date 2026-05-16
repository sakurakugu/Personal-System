"""文章搜索条件服务。"""

from __future__ import annotations

from sqlalchemy import or_

from app.modules.users.models import 用户
from app.modules.articles.models import 文章


def 构建文章搜索条件(search: str | None, user: 用户 | None):
    """构建文章搜索条件。"""
    normalized_search = (search or "").strip()
    if not normalized_search:
        return None

    keyword = f"%{normalized_search}%"
    if user is None:
        return 文章.title.ilike(keyword)

    return or_(
        文章.title.ilike(keyword),
        文章.excerpt.ilike(keyword),
        文章.content.ilike(keyword),
    )
