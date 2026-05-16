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
from app.modules.articles.models import 文章, 文章状态


def 文章查询():
    """构建文章详情查询。"""
    return (
        select(文章)
        .options(
            selectinload(文章.author),
            selectinload(文章.category),
            selectinload(文章.tags),
        )
    )


def 排序文章用于导航(articles: list[文章]) -> list[文章]:
    """按详情页导航使用的顺序排序文章。"""
    return sorted(
        articles,
        key=lambda article: article.published_at or article.created_at,
        reverse=True,
    )


def 构建唯一标识(base_slug: str, *, exists: bool, now: datetime | None = None) -> str:
    """按冲突情况生成唯一 slug。"""
    if not exists:
        return base_slug
    current_time = now or utcnow()
    return f"{base_slug}-{int(current_time.timestamp())}"


def 构建文章基础标识(title: str, article_id: UUID) -> str:
    """根据标题生成文章基础 slug。"""
    normalized_title = title.strip()
    if not normalized_title:
        return f"draft-{article_id}"
    generated_slug = slugify(normalized_title)
    return generated_slug or f"draft-{article_id}"


async def 构建可用文章标识(
    db: AsyncSession,
    title: str,
    article_id: UUID,
    *,
    current_article_id: UUID | None = None,
    now: datetime | None = None,
) -> str:
    """生成当前可用的文章 slug。"""
    base_slug = 构建文章基础标识(title, article_id)
    if base_slug.startswith("draft-"):
        return base_slug

    query = select(文章.id).where(文章.slug == base_slug)
    if current_article_id is not None:
        query = query.where(文章.id != current_article_id)

    existing = await db.execute(query)
    return 构建唯一标识(base_slug, exists=existing.scalar_one_or_none() is not None, now=now)


def 解析文章状态(value: str) -> 文章状态:
    """解析文章状态。"""
    try:
        return 文章状态(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的文章状态") from exc


def 应用文章状态(
    article: 文章,
    status: 文章状态,
    *,
    now: datetime | None = None,
) -> None:
    """同步文章状态与发布时间字段。"""
    article.status = status
    if status in (文章状态.public, 文章状态.login_required):
        article.published_at = article.published_at or (now or utcnow())
        return
    article.published_at = None


def 应用文章删除状态(article: 文章, *, now: datetime | None = None) -> None:
    """将文章标记为已删除。"""
    article.is_deleted = True
    article.deleted_at = now or utcnow()


def 恢复文章删除状态(article: 文章) -> None:
    """恢复文章删除状态。"""
    article.is_deleted = False
    article.deleted_at = None


def 刷新文章最后编辑时间(article: 文章, *, now: datetime | None = None) -> None:
    """刷新文章最后编辑时间。"""
    article.last_edited_at = now or utcnow()
