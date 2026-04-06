"""文章领域服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus, ArticleTag, Tag
from app.models.feed import FeedItemType
from app.models.user import User, UserRole
from app.schemas.article import ArticleCreate, ArticleListItem, ArticleUpdate
from app.schemas.shared import PaginatedResponse
from app.services.feed_service import delete_feed_item, sync_article_feed_item


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def article_query():
    """构建文章详情查询。"""
    return (
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.category),
            selectinload(Article.tags),
        )
    )


def build_unique_slug(base_slug: str, *, exists: bool, now: datetime | None = None) -> str:
    """按冲突情况生成唯一 slug。"""
    if not exists:
        return base_slug
    current_time = now or utcnow()
    return f"{base_slug}-{int(current_time.timestamp())}"


def parse_article_status(value: str) -> ArticleStatus:
    """解析文章状态。"""
    try:
        return ArticleStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的文章状态") from exc


def apply_article_status(
    article: Article,
    status: ArticleStatus,
    *,
    now: datetime | None = None,
) -> None:
    """同步文章状态与发布时间字段。"""
    article.status = status
    if status in (ArticleStatus.public, ArticleStatus.login_required):
        article.published_at = article.published_at or (now or utcnow())
        return
    article.published_at = None


def can_user_read_article(article: Article, user: User | None) -> bool:
    """判断当前用户是否可查看文章。"""
    if article.status == ArticleStatus.public:
        return True
    if article.status == ArticleStatus.login_required:
        return user is not None
    if user is None:
        return False
    if article.author_id == user.id:
        return True
    return user.role in (UserRole.admin, UserRole.super_admin)


def can_user_see_article_in_blog(article: Article, user: User | None) -> bool:
    """判断当前用户是否可在博客列表中看到文章。"""
    if article.status in (ArticleStatus.public, ArticleStatus.login_required):
        return article.status == ArticleStatus.public or user is not None
    return (
        user is not None
        and article.author_id == user.id
        and user.settings is not None
        and user.settings.show_private_articles_on_home
    )


def build_blog_visible_article_clause(user: User | None):
    """构建博客列表可见文章条件。"""
    if user is None:
        return Article.status == ArticleStatus.public
    if user.settings is None or not user.settings.show_private_articles_on_home:
        return Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
    return or_(
        Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
        and_(
            Article.status == ArticleStatus.private,
            Article.author_id == user.id,
        ),
    )


def ensure_article_write_permission(article: Article, user: User) -> None:
    """校验当前用户是否可修改文章。"""
    if article.author_id == user.id:
        return
    if user.role in (UserRole.admin, UserRole.super_admin):
        return
    raise HTTPException(status_code=403, detail="无权操作")


async def replace_article_tags(db: AsyncSession, article_id: str, tag_ids: list[str]) -> None:
    """替换文章标签关联。"""
    await db.execute(delete(ArticleTag).where(ArticleTag.article_id == article_id))
    for tag_id in tag_ids:
        db.add(ArticleTag(article_id=article_id, tag_id=tag_id))


async def get_article_or_404(db: AsyncSession, article_id: str) -> Article:
    """按 ID 获取文章。"""
    result = await db.execute(article_query().where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def get_my_article(db: AsyncSession, article_id: str, user: User) -> Article:
    """获取当前用户自己的文章。"""
    result = await db.execute(
        article_query().where(Article.id == article_id, Article.author_id == user.id)
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def list_articles(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: User | None,
    category: str | None,
    tag: str | None,
    search: str | None,
) -> PaginatedResponse:
    """获取公开文章列表。"""
    query = article_query().where(build_blog_visible_article_clause(user))
    if category:
        query = query.where(Article.category.has(slug=category))
    if tag:
        query = query.where(Article.tags.any(Tag.slug == tag))
    if search:
        query = query.where(Article.title.ilike(f"%{search}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(func.coalesce(Article.published_at, Article.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[ArticleListItem.model_validate(item) for item in items],
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


async def create_article(db: AsyncSession, body: ArticleCreate, user: User) -> Article:
    """创建文章。"""
    base_slug = slugify(body.title)
    existing = await db.execute(select(Article.id).where(Article.slug == base_slug))
    status = parse_article_status(body.status)
    article = Article(
        title=body.title,
        slug=build_unique_slug(base_slug, exists=existing.scalar_one_or_none() is not None),
        content=body.content,
        excerpt=body.excerpt,
        cover_url=body.cover_url,
        status=status,
        author_id=user.id,
        category_id=body.category_id,
    )
    apply_article_status(article, status)
    db.add(article)
    await db.flush()

    if body.tag_ids:
        await replace_article_tags(db, str(article.id), [str(tag_id) for tag_id in body.tag_ids])
        await db.flush()

    await sync_article_feed_item(db, article)
    await db.flush()

    return await get_article_or_404(db, str(article.id))


async def update_article(db: AsyncSession, article_id: str, body: ArticleUpdate, user: User) -> Article:
    """更新文章。"""
    article = await get_article_or_404(db, article_id)
    ensure_article_write_permission(article, user)

    data = body.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    status_value = data.pop("status", None)

    for key, value in data.items():
        setattr(article, key, value)

    if status_value is not None:
        apply_article_status(article, parse_article_status(status_value))

    if tag_ids is not None:
        await replace_article_tags(db, article_id, [str(tag_id) for tag_id in tag_ids])

    await sync_article_feed_item(db, article)
    await db.flush()
    return await get_article_or_404(db, article_id)


async def delete_article(db: AsyncSession, article_id: str, user: User) -> None:
    """删除文章。"""
    article = await get_article_or_404(db, article_id)
    ensure_article_write_permission(article, user)
    await delete_feed_item(db, FeedItemType.article, article.id)
    await db.delete(article)
