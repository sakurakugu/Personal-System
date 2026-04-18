"""文章 Schema 兼容入口。"""

from app.modules.articles.schemas import (
    ArticleCreate,
    ArticleDraftCreate,
    ArticleImageRead,
    ArticleListItem,
    ArticleMetaRead,
    ArticleNavigationRead,
    ArticleRead,
    ArticleRelatedResponse,
    ArticleUpdate,
    CategoryCreate,
    CategoryRead,
    TagCreate,
    TagRead,
)

__all__ = [
    "ArticleCreate",
    "ArticleDraftCreate",
    "ArticleImageRead",
    "ArticleListItem",
    "ArticleMetaRead",
    "ArticleNavigationRead",
    "ArticleRead",
    "ArticleRelatedResponse",
    "ArticleUpdate",
    "CategoryCreate",
    "CategoryRead",
    "TagCreate",
    "TagRead",
]
