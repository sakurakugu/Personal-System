"""文章领域服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleImage, ArticleStatus, ArticleTag, Category, Tag
from app.models.feed import FeedItemType
from app.models.user import User, UserRole
from app.schemas.article import ArticleCreate, ArticleDraftCreate, ArticleListItem, ArticleUpdate
from app.schemas.shared import PaginatedResponse
from app.services.article_search_service import build_article_search_clause
from app.services.article_schema_service import build_article_list_item_response
from app.services.feed_service import delete_feed_item, invalidate_feed_home_cache, sync_article_feed_item
from app.services.stats_service import invalidate_blog_stats_cache
from app.services.storage_service import remove_objects_best_effort
from app.utils.uuid import generate_uuid7


def _strip_code_blocks(text: str) -> str:
    """移除 fenced code blocks 和 inline code（在转 HTML 前先清掉，避免代码被算进正文）。"""
    import re

    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def calculate_word_count(markdown_text: str | None) -> int:
    """
    计算 Markdown 文章的可读字数。
    流程：去代码块 -> Markdown 转 HTML -> 去 HTML 标签 -> 统计中英文。
    """
    import re

    from bs4 import BeautifulSoup

    if not markdown_text:
        return 0

    cleaned = _strip_code_blocks(markdown_text)

    import markdown as md_lib

    html = md_lib.markdown(cleaned)
    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text(separator=" ")
    plain_text = re.sub(r"\s+", " ", plain_text).strip()

    chinese_chars = re.findall(r"[\u4e00-\u9fa5]", plain_text)
    english_chars = re.findall(r"[a-zA-Z]", plain_text)
    return len(chinese_chars) + len(english_chars)


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


def sort_articles_for_navigation(articles: list[Article]) -> list[Article]:
    """按详情页导航使用的顺序排序文章。"""
    return sorted(
        articles,
        key=lambda article: article.published_at or article.created_at,
        reverse=True,
    )


def build_unique_slug(base_slug: str, *, exists: bool, now: datetime | None = None) -> str:
    """按冲突情况生成唯一 slug。"""
    if not exists:
        return base_slug
    current_time = now or utcnow()
    return f"{base_slug}-{int(current_time.timestamp())}"


def build_article_base_slug(title: str, article_id: UUID) -> str:
    """根据标题生成文章基础 slug。"""
    normalized_title = title.strip()
    if not normalized_title:
        return f"draft-{article_id}"
    generated_slug = slugify(normalized_title)
    return generated_slug or f"draft-{article_id}"


async def build_available_article_slug(
    db: AsyncSession,
    title: str,
    article_id: UUID,
    *,
    current_article_id: UUID | None = None,
    now: datetime | None = None,
) -> str:
    """生成当前可用的文章 slug。"""
    base_slug = build_article_base_slug(title, article_id)
    if base_slug.startswith("draft-"):
        return base_slug

    query = select(Article.id).where(Article.slug == base_slug)
    if current_article_id is not None:
        query = query.where(Article.id != current_article_id)

    existing = await db.execute(query)
    return build_unique_slug(base_slug, exists=existing.scalar_one_or_none() is not None, now=now)


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


def touch_article_last_edited_at(article: Article, *, now: datetime | None = None) -> None:
    """刷新文章最后编辑时间。"""
    article.last_edited_at = now or utcnow()


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
    """获取所有可见文章的最小元数据（用于日历、归档等）。"""
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
    """按 slug 获取文章（不增加浏览量），用于推荐接口。"""
    result = await db.execute(article_query().where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not can_user_read_article(article, user):
        if article.status == ArticleStatus.login_required:
            raise HTTPException(status_code=401, detail="该文章需要登录后查看")
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def get_related_and_random_articles(
    db: AsyncSession,
    slug: str,
    user: User | None,
) -> tuple[Article | None, Article | None, list[Article], list[Article]]:
    """获取上一篇、下一篇、相关文章和随机推荐文章。"""
    import random

    current = await get_article_for_related(db, slug, user)
    all_articles = await list_all_article_meta(db, user=user)
    sorted_articles = sort_articles_for_navigation(all_articles)

    current_tag_names = {t.name for t in current.tags}
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

    others = [a for a in all_articles if a.id != current.id]

    scored: list[tuple[Article, float]] = []
    for article in others:
        score = 0.0
        if article.category and article.category.name == current_category_name:
            score += 10.0
        article_tag_names = {t.name for t in article.tags}
        shared_tags = len(current_tag_names & article_tag_names)
        score += shared_tags * 5.0
        score += (article.view_count or 0) * 0.01
        scored.append((article, score))

    scored.sort(
        key=lambda x: (
            -x[1],
            -(x[0].published_at or x[0].created_at).timestamp(),
        )
    )
    related = [a for a, _ in scored[:5]]

    related_ids = {a.id for a in related}
    pool = [a for a in others if a.id not in related_ids]
    k = min(5, len(pool))
    random_articles = random.sample(pool, k) if k > 0 else []

    return prev_article, next_article, related, random_articles


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
