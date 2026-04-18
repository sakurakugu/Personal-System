"""文章模型兼容入口。"""

from app.modules.articles.models import Article, ArticleImage, ArticleStatus, ArticleTag, Category, Tag

__all__ = [
    "Article",
    "ArticleImage",
    "ArticleStatus",
    "ArticleTag",
    "Category",
    "Tag",
]
