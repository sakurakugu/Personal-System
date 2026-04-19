"""文章查询与推荐。"""

from __future__ import annotations

import math
import random
from uuid import UUID

from fastapi import HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.articles.models import Article, ArticleImage, ArticleStatus, Tag
from app.modules.articles.permissions import (
    build_blog_visible_article_clause,
    can_user_read_article,
)
from app.modules.articles.schema import build_article_list_item_response
from app.modules.articles.schemas import ArticleLikeRead, ArticleListItem
from app.modules.articles.search import build_article_search_clause
from app.modules.articles.workflow import (
    article_query,
    sort_articles_for_navigation,
)
from app.modules.users.models import User
from app.shared.engagement import (
    add_set_member_once,
    ensure_visitor_id,
    get_visitor_id,
    has_set_member,
    remove_set_member,
)
from app.shared.kernel.pagination import PaginatedResponse


async def get_article_or_404(db: AsyncSession, article_id: str) -> Article:
    """按 ID 获取文章。"""
    result = await db.execute(article_query().where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def list_article_image_storage_keys(db: AsyncSession, article_id: UUID) -> list[str]:
    """获取文章关联的全部图片对象键。"""
    result = await db.execute(
        select(ArticleImage.storage_key).where(ArticleImage.article_id == article_id)
    )
    return list(result.scalars().all())


async def get_my_article(db: AsyncSession, article_id: str, user: User) -> Article:
    """获取当前用户自己的文章。"""
    result = await db.execute(
        article_query().where(Article.id == article_id, Article.author_id == user.id)
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def list_all_article_meta(
    db: AsyncSession,
    *,
    user: User | None,
) -> list[Article]:
    """获取所有可见文章的最小元数据。"""
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.tags), selectinload(Article.category))
        .where(build_blog_visible_article_clause(user))
        .order_by(func.coalesce(Article.published_at, Article.created_at).desc())
    )
    return list(result.scalars().all())


async def list_articles(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: User | None,
    category: str | None,
    tag: str | None,
    search: str | None,
    sign_cover_url: bool = False,
) -> PaginatedResponse:
    """获取公开文章列表。"""
    query = article_query().where(build_blog_visible_article_clause(user))
    if category:
        query = query.where(Article.category.has(slug=category))
    if tag:
        query = query.where(Article.tags.any(Tag.slug == tag))
    搜索条件 = build_article_search_clause(search, user)
    if 搜索条件 is not None:
        query = query.where(搜索条件)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(func.coalesce(Article.published_at, Article.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[build_article_list_item_response(item, sign_cover_url=sign_cover_url) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def list_my_articles(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: User,
) -> PaginatedResponse:
    """获取当前用户的文章列表。"""
    query = article_query().where(Article.author_id == user.id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(Article.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[ArticleListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_article_by_slug(db: AsyncSession, slug: str, user: User | None) -> Article:
    """按 slug 获取当前用户可访问的文章详情，并增加浏览量。"""
    result = await db.execute(article_query().where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not can_user_read_article(article, user):
        if article.status == ArticleStatus.login_required:
            raise HTTPException(status_code=401, detail="该文章需要登录后查看")
        raise HTTPException(status_code=404, detail="文章不存在")
    article.view_count += 1
    await db.flush()
    return article


async def get_article_for_related(db: AsyncSession, slug: str, user: User | None) -> Article:
    """按 slug 获取文章，不增加浏览量。"""
    result = await db.execute(article_query().where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not can_user_read_article(article, user):
        if article.status == ArticleStatus.login_required:
            raise HTTPException(status_code=401, detail="该文章需要登录后查看")
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def like_article_by_slug(
    db: AsyncSession,
    slug: str,
    user: User | None,
    request: Request,
    response: Response,
) -> ArticleLikeRead:
    """按 slug 点赞文章，并基于匿名访客标识去重。"""
    article = await get_article_for_related(db, slug, user)
    visitor_id = ensure_visitor_id(request, response)
    changed = await add_set_member_once(f"like:article:{article.id}", visitor_id)
    if changed:
        article.like_count += 1
        await db.flush()
    return ArticleLikeRead(like_count=article.like_count, changed=changed, liked=True)


async def unlike_article_by_slug(
    db: AsyncSession,
    slug: str,
    user: User | None,
    request: Request,
) -> ArticleLikeRead:
    """按 slug 取消点赞文章。"""
    article = await get_article_for_related(db, slug, user)
    visitor_id = get_visitor_id(request)
    if not visitor_id:
        return ArticleLikeRead(like_count=article.like_count, changed=False, liked=False)

    changed = await remove_set_member(f"like:article:{article.id}", visitor_id)
    if changed:
        article.like_count = max(0, article.like_count - 1)
        await db.flush()
    return ArticleLikeRead(like_count=article.like_count, changed=changed, liked=False)


async def is_article_liked_by_visitor(article_id: UUID, request: Request) -> bool:
    """判断当前匿名访客是否已点赞文章。"""
    visitor_id = get_visitor_id(request)
    if not visitor_id:
        return False
    return await has_set_member(f"like:article:{article_id}", visitor_id)


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
