"""文章 CRUD 路由。

此模块提供文章的管理接口，包括：
- 公开接口：获取已发布文章列表、查看文章详情
- 用户接口：创建、更新、删除自己的文章
- 支持分类、标签筛选和搜索
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from slugify import slugify
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Article, ArticleStatus, ArticleTag, Tag, User
from app.schemas.schemas import (
    ArticleCreate,
    ArticleListItem,
    ArticleRead,
    ArticleUpdate,
    PaginatedResponse,
)

# 创建路由器，前缀为 /articles，标签为 articles
router = APIRouter(prefix="/articles", tags=["articles"])


def _article_query():
    """
    构建文章基础查询，预加载关联数据。

    Returns:
        Select: SQLAlchemy 查询对象，已预加载 author、category、tags
    """
    return (
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.category),
            selectinload(Article.tags),
        )
    )


@router.get("", response_model=PaginatedResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取已发布文章列表（公开接口）。

    支持按分类、标签筛选和标题搜索。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量，范围 1-50
        category: 分类 slug，可选
        tag: 标签 slug，可选
        search: 搜索关键词（标题模糊匹配），可选
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的文章列表
    """
    q = _article_query().where(Article.status == ArticleStatus.published)

    if category:
        q = q.where(Article.category.has(slug=category))
    if tag:
        q = q.where(Article.tags.any(Tag.slug == tag))
    if search:
        q = q.where(Article.title.ilike(f"%{search}%"))

    # 总数
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Article.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().unique().all()

    return PaginatedResponse(
        items=[ArticleListItem.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/my/list", response_model=PaginatedResponse)
async def list_my_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的文章列表（包括草稿和已发布）。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量，范围 1-50
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的文章列表
    """
    q = _article_query().where(Article.author_id == user.id)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(Article.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().unique().all()

    return PaginatedResponse(
        items=[ArticleListItem.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/my/{article_id}", response_model=ArticleRead)
async def get_my_article(
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的指定文章（包括草稿）。

    Args:
        article_id: 文章 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        ArticleRead: 文章详情

    Raises:
        HTTPException: 404 - 文章不存在
    """
    result = await db.execute(
        _article_query().where(Article.id == article_id, Article.author_id == user.id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


@router.get("/{slug}", response_model=ArticleRead)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    """
    根据 slug 获取文章详情（公开接口）。

    访问时自动增加文章浏览量。

    Args:
        slug: 文章 slug
        db: 数据库会话

    Returns:
        ArticleRead: 文章详情

    Raises:
        HTTPException: 404 - 文章不存在
    """
    result = await db.execute(_article_query().where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    # 增加浏览量
    article.view_count += 1
    await db.flush()
    return article


@router.post("", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
    body: ArticleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新文章。

    自动根据标题生成唯一 slug，支持设置分类和标签。

    Args:
        body: 文章创建数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        ArticleRead: 创建的文章
    """
    base_slug = slugify(body.title)
    # 确保 slug 唯一：如果已存在，则添加时间戳后缀
    existing = await db.execute(select(Article).where(Article.slug == base_slug))
    slug = base_slug if not existing.scalar_one_or_none() else f"{base_slug}-{int(datetime.now(timezone.utc).timestamp())}"

    article = Article(
        title=body.title,
        slug=slug,
        content=body.content,
        excerpt=body.excerpt,
        cover_url=body.cover_url,
        status=ArticleStatus(body.status),
        author_id=user.id,
        category_id=body.category_id,
    )
    if body.status == "published":
        article.published_at = datetime.now(timezone.utc)

    db.add(article)
    await db.flush()

    # 标签
    if body.tag_ids:
        for tid in body.tag_ids:
            db.add(ArticleTag(article_id=article.id, tag_id=tid))
        await db.flush()

    # 重新加载关联数据
    result = await db.execute(_article_query().where(Article.id == article.id))
    return result.scalar_one()


@router.patch("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: str,
    body: ArticleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新文章。

    只有文章作者或管理员可以更新。
    如果文章从草稿变为发布状态，自动设置发布时间。

    Args:
        article_id: 文章 ID
        body: 文章更新数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        ArticleRead: 更新后的文章

    Raises:
        HTTPException: 404 - 文章不存在
        HTTPException: 403 - 无权操作
    """
    result = await db.execute(_article_query().where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="无权操作")

    data = body.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)

    for k, v in data.items():
        if k == "status" and v == "published" and article.published_at is None:
            article.published_at = datetime.now(timezone.utc)
        setattr(article, k, v)

    if tag_ids is not None:
        # 替换标签：先删除原有标签关联，再添加新标签
        await db.execute(delete(ArticleTag).where(ArticleTag.article_id == article.id))
        for tid in tag_ids:
            db.add(ArticleTag(article_id=article.id, tag_id=tid))

    await db.flush()
    result = await db.execute(_article_query().where(Article.id == article.id))
    return result.scalar_one()


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除文章。

    只有文章作者或管理员可以删除。

    Args:
        article_id: 文章 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 文章不存在
        HTTPException: 403 - 无权操作
    """
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.author_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="无权操作")
    await db.delete(article)
