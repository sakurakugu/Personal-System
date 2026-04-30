"""文章状态、slug 与基础查询辅助。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.articles.content import utcnow
from app.modules.articles.models import Article, ArticleStatus


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
