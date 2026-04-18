"""文章服务兼容入口。"""

from __future__ import annotations

import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.user import User
from app.modules.articles.content import calculate_word_count, utcnow
from app.modules.articles.crud import create_article, create_article_draft, delete_article, replace_article_tags
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
    list_all_article_meta,
    list_article_image_storage_keys,
    list_articles,
    list_my_articles,
)
from app.modules.articles.workflow import (
    apply_article_status,
    build_available_article_slug,
    build_unique_slug,
    parse_article_status,
    sort_articles_for_navigation,
    touch_article_last_edited_at,
)
from app.schemas.article import ArticleUpdate
from app.services.feed_service import invalidate_feed_home_cache, sync_article_feed_item
from app.services.stats_service import invalidate_blog_stats_cache


async def update_article(db: AsyncSession, article_id: str, body: ArticleUpdate, user: User):
    """更新文章。"""
    article = await get_article_or_404(db, article_id)
    ensure_article_write_permission(article, user)

    data = body.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    status_value = data.pop("status", None)
    current_time = utcnow()
    new_title = data.get("title")
    old_category_id = article.category_id

    for key, value in data.items():
        setattr(article, key, value)

    if "content" in data:
        article.word_count = calculate_word_count(article.content)

    if new_title is not None and article.slug.startswith("draft-"):
        article.slug = await build_available_article_slug(
            db,
            new_title,
            article.id,
            current_article_id=article.id,
            now=current_time,
        )

    if status_value is not None:
        apply_article_status(article, parse_article_status(status_value), now=current_time)

    if tag_ids is not None:
        await replace_article_tags(db, article_id, [str(tag_id) for tag_id in tag_ids])

    new_category_id = article.category_id
    if "category_id" in data and old_category_id != new_category_id:
        from sqlalchemy import update

        from app.models.article import Category

        if old_category_id is not None:
            await db.execute(
                update(Category)
                .where(Category.id == old_category_id)
                .values(article_count=Category.article_count - 1)
            )
        if new_category_id is not None:
            await db.execute(
                update(Category)
                .where(Category.id == new_category_id)
                .values(article_count=Category.article_count + 1)
            )

    touch_article_last_edited_at(article, now=current_time)
    await sync_article_feed_item(db, article)
    await db.flush()

    await invalidate_feed_home_cache()
    await invalidate_blog_stats_cache()
    return await get_article_or_404(db, article_id)


async def get_related_and_random_articles(
    db: AsyncSession,
    slug: str,
    user: User | None,
) -> tuple[Article | None, Article | None, list[Article], list[Article]]:
    """获取上一篇、下一篇、相关文章和随机推荐文章。"""
    current = await get_article_for_related(db, slug, user)
    all_articles = await list_all_article_meta(db, user=user)
    sorted_articles = sort_articles_for_navigation(all_articles)

    current_tag_names = {tag.name for tag in current.tags}
    current_category_name = current.category.name if current.category else None
    current_index = next(
        (index for index, article in enumerate(sorted_articles) if article.id == current.id),
        -1,
    )
    prev_article = sorted_articles[current_index - 1] if current_index > 0 else None
    next_article = (
        sorted_articles[current_index + 1]
        if current_index != -1 and current_index < len(sorted_articles) - 1
        else None
    )

    others = [article for article in all_articles if article.id != current.id]

    scored: list[tuple[Article, float]] = []
    for article in others:
        score = 0.0
        if article.category and article.category.name == current_category_name:
            score += 10.0
        article_tag_names = {tag.name for tag in article.tags}
        shared_tags = len(current_tag_names & article_tag_names)
        score += shared_tags * 5.0
        score += (article.view_count or 0) * 0.01
        scored.append((article, score))

    scored.sort(
        key=lambda item: (
            -item[1],
            -(item[0].published_at or item[0].created_at).timestamp(),
        )
    )
    related = [article for article, _ in scored[:5]]

    related_ids = {article.id for article in related}
    pool = [article for article in others if article.id not in related_ids]
    k = min(5, len(pool))
    random_articles = random.sample(pool, k) if k > 0 else []

    return prev_article, next_article, related, random_articles


__all__ = [
    "apply_article_status",
    "build_blog_visible_article_clause",
    "build_unique_slug",
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
    "invalidate_blog_stats_cache",
    "invalidate_feed_home_cache",
    "list_all_article_meta",
    "list_article_image_storage_keys",
    "list_articles",
    "list_my_articles",
    "parse_article_status",
    "replace_article_tags",
    "sort_articles_for_navigation",
    "sync_article_feed_item",
    "touch_article_last_edited_at",
    "update_article",
    "utcnow",
]
