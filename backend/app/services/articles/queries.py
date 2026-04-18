"""文章查询兼容入口。"""

from app.modules.articles.queries import (
    get_article_by_slug,
    get_article_for_related,
    get_article_or_404,
    get_my_article,
    get_related_and_random_articles,
    list_all_article_meta,
    list_article_image_storage_keys,
    list_articles,
    list_my_articles,
)

__all__ = [
    "get_article_by_slug",
    "get_article_for_related",
    "get_article_or_404",
    "get_my_article",
    "get_related_and_random_articles",
    "list_all_article_meta",
    "list_article_image_storage_keys",
    "list_articles",
    "list_my_articles",
]
