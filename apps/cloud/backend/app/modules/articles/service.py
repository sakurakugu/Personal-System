"""文章模块公开服务入口。"""

from app.modules.articles.content import calculate_word_count, utcnow
from app.modules.articles.crud import create_article, create_article_draft, delete_article, replace_article_tags, update_article
from app.modules.articles.image import (
    build_article_image_directory,
    build_article_image_read,
    list_article_images,
    upload_article_image,
)
from app.modules.articles.permissions import (
    build_blog_visible_article_clause,
    can_user_read_article,
    can_user_see_article_in_blog,
    ensure_article_write_permission,
)
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
from app.modules.articles.schema import build_article_list_item_response, build_article_read_response
from app.modules.articles.search import build_article_search_clause
from app.modules.articles.workflow import (
    apply_article_status,
    article_query,
    build_article_base_slug,
    build_available_article_slug,
    build_unique_slug,
    parse_article_status,
    sort_articles_for_navigation,
    touch_article_last_edited_at,
)

__all__ = [
    "apply_article_status",
    "article_query",
    "build_article_base_slug",
    "build_article_image_directory",
    "build_article_image_read",
    "build_article_list_item_response",
    "build_article_read_response",
    "build_article_search_clause",
    "build_available_article_slug",
    "build_blog_visible_article_clause",
    "build_unique_slug",
    "calculate_word_count",
    "can_user_read_article",
    "can_user_see_article_in_blog",
    "create_article",
    "create_article_draft",
    "delete_article",
    "ensure_article_write_permission",
    "get_article_by_slug",
    "get_article_for_related",
    "get_article_or_404",
    "get_my_article",
    "get_related_and_random_articles",
    "list_all_article_meta",
    "list_article_image_storage_keys",
    "list_article_images",
    "list_articles",
    "list_my_articles",
    "parse_article_status",
    "replace_article_tags",
    "sort_articles_for_navigation",
    "touch_article_last_edited_at",
    "update_article",
    "upload_article_image",
    "utcnow",
]
