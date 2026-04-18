"""分类和标签路由兼容入口。"""

from app.modules.articles.taxonomy_api import (
    create_category,
    create_tag,
    delete_category,
    delete_tag,
    list_categories,
    list_tags,
    router,
)

__all__ = [
    "create_category",
    "create_tag",
    "delete_category",
    "delete_tag",
    "list_categories",
    "list_tags",
    "router",
]
