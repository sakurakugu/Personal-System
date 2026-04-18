"""文章 CRUD 编排。"""

from __future__ import annotations

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.articles.content import calculate_word_count, utcnow
from app.modules.feed.models import FeedItemType
from app.modules.feed.service import delete_feed_item, invalidate_feed_home_cache, sync_article_feed_item
from app.modules.articles.models import Article, ArticleStatus, ArticleTag, Category
from app.modules.articles.permissions import ensure_article_write_permission
from app.modules.articles.queries import (
    get_article_or_404,
    list_article_image_storage_keys,
)
from app.modules.articles.schemas import ArticleCreate, ArticleDraftCreate, ArticleUpdate
from app.modules.articles.workflow import (
    apply_article_status,
    build_available_article_slug,
    parse_article_status,
    touch_article_last_edited_at,
)
from app.modules.stats.service import invalidate_blog_stats_cache
from app.services.storage_service import remove_objects_best_effort
from app.utils.uuid import generate_uuid7


async def replace_article_tags(db: AsyncSession, article_id: str, tag_ids: list[str]) -> None:
    """替换文章标签关联。"""
    await db.execute(delete(ArticleTag).where(ArticleTag.article_id == article_id))
    for tag_id in tag_ids:
        db.add(ArticleTag(article_id=article_id, tag_id=tag_id))


async def create_article(db: AsyncSession, body: ArticleCreate, user: User) -> Article:
    """创建文章。"""
    status = parse_article_status(body.status)
    current_time = utcnow()
    article_id = generate_uuid7()
    article = Article(
        id=article_id,
        title=body.title,
        slug=await build_available_article_slug(db, body.title, article_id, now=current_time),
        content=body.content,
        excerpt=body.excerpt,
        cover_url=body.cover_url,
        status=status,
        word_count=calculate_word_count(body.content),
        author_id=user.id,
        category_id=body.category_id,
        last_edited_at=current_time,
    )
    apply_article_status(article, status, now=current_time)
    db.add(article)
    await db.flush()

    if body.tag_ids:
        await replace_article_tags(db, str(article.id), [str(tag_id) for tag_id in body.tag_ids])
        await db.flush()

    if body.category_id is not None:
        await db.execute(
            update(Category)
            .where(Category.id == body.category_id)
            .values(article_count=Category.article_count + 1)
        )

    await sync_article_feed_item(db, article)
    await db.flush()

    await invalidate_feed_home_cache()
    await invalidate_blog_stats_cache()
    return await get_article_or_404(db, str(article.id))


async def create_article_draft(db: AsyncSession, body: ArticleDraftCreate | None, user: User) -> Article:
    """创建文章草稿占位。"""
    payload = body or ArticleDraftCreate()
    current_time = utcnow()
    article_id = generate_uuid7()
    article = Article(
        id=article_id,
        title=payload.title or "",
        slug=await build_available_article_slug(db, payload.title or "", article_id, now=current_time),
        content=payload.content or "",
        excerpt=payload.excerpt,
        cover_url=payload.cover_url,
        status=ArticleStatus.private,
        word_count=calculate_word_count(payload.content or ""),
        author_id=user.id,
        category_id=payload.category_id,
        last_edited_at=current_time,
    )
    apply_article_status(article, ArticleStatus.private, now=current_time)
    db.add(article)
    await db.flush()

    if payload.tag_ids:
        await replace_article_tags(db, str(article.id), [str(tag_id) for tag_id in payload.tag_ids])
        await db.flush()

    return await get_article_or_404(db, str(article.id))


async def update_article(db: AsyncSession, article_id: str, body: ArticleUpdate, user: User) -> Article:
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


async def delete_article(db: AsyncSession, article_id: str, user: User) -> None:
    """删除文章。"""
    article = await get_article_or_404(db, article_id)
    ensure_article_write_permission(article, user)
    image_storage_keys = await list_article_image_storage_keys(db, article.id)
    category_id = article.category_id
    await delete_feed_item(db, FeedItemType.article, article.id)
    await db.delete(article)

    if category_id is not None:
        await db.execute(
            update(Category)
            .where(Category.id == category_id)
            .values(article_count=Category.article_count - 1)
        )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await invalidate_feed_home_cache()
    await invalidate_blog_stats_cache()
    remove_objects_best_effort(image_storage_keys)
