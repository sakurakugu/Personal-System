"""文章搜索条件服务。"""

from __future__ import annotations

from sqlalchemy import or_

from app.models.article import Article
from app.models.user import User


def build_article_search_clause(search: str | None, user: User | None):
    """构建文章搜索条件。"""
    normalized_search = (search or "").strip()
    if not normalized_search:
        return None

    keyword = f"%{normalized_search}%"
    if user is None:
        return Article.title.ilike(keyword)

    return or_(
        Article.title.ilike(keyword),
        Article.excerpt.ilike(keyword),
        Article.content.ilike(keyword),
    )
