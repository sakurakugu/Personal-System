"""文章 CRUD 兼容入口。"""

from app.modules.articles.crud import create_article, create_article_draft, delete_article, replace_article_tags, update_article

__all__ = [
    "create_article",
    "create_article_draft",
    "delete_article",
    "replace_article_tags",
    "update_article",
]
