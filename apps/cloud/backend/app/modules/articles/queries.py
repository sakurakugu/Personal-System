"""文章查询与推荐。"""

from __future__ import annotations

import math
import random
from uuid import UUID

from fastapi import HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.articles.models import 文章, 文章图片, 文章状态, 标签
from app.modules.articles.permissions import (
    构建博客可见文章条件,
    用户可否阅读文章,
)
from app.modules.articles.schema import 构建文章列表项响应
from app.modules.articles.schemas import 文章点赞信息, 文章列表项
from app.modules.articles.search import 构建文章搜索条件
from app.modules.articles.workflow import (
    文章查询,
    排序文章用于导航,
)
from app.modules.users.models import 用户
from app.shared.engagement import (
    单次添加集合成员,
    包含集合成员,
    确保访客ID,
    获取访客ID,
    移除集合成员,
)
from app.shared.kernel.pagination import PaginatedResponse

全部文章分类筛选值 = "all"
未分类文章分类筛选值 = "uncategorized"


async def 获取文章或404(db: AsyncSession, article_id: str) -> 文章:
    """按 ID 获取文章。"""
    result = await db.execute(
        文章查询().where(
            文章.id == article_id,
            文章.is_deleted.is_(False),
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def 获取已删除文章或404(db: AsyncSession, article_id: str) -> 文章:
    """按 ID 获取回收站中的文章。"""
    result = await db.execute(
        文章查询().where(
            文章.id == article_id,
            文章.is_deleted.is_(True),
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在或未被删除")
    return article


async def 列出文章图片存储键(db: AsyncSession, article_id: UUID) -> list[str]:
    """获取文章关联的全部图片对象键。"""
    result = await db.execute(
        select(文章图片.storage_key).where(文章图片.article_id == article_id)
    )
    return list(result.scalars().all())


async def 获取我的文章(db: AsyncSession, article_id: str, user: 用户) -> 文章:
    """获取当前用户自己的文章。"""
    result = await db.execute(
        文章查询().where(
            文章.id == article_id,
            文章.author_id == user.id,
            文章.is_deleted.is_(False),
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def 获取我删除的文章(db: AsyncSession, article_id: str, user: 用户) -> 文章:
    """获取当前用户回收站中的文章。"""
    result = await db.execute(
        文章查询().where(
            文章.id == article_id,
            文章.author_id == user.id,
            文章.is_deleted.is_(True),
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def 列出全部文章元数据(
    db: AsyncSession,
    *,
    user: 用户 | None,
) -> list[文章]:
    """获取所有可见文章的最小元数据。"""
    result = await db.execute(
        select(文章)
        .options(
            selectinload(文章.author),
            selectinload(文章.tags),
            selectinload(文章.category),
        )
        .where(构建博客可见文章条件(user))
        .order_by(func.coalesce(文章.published_at, 文章.created_at).desc())
    )
    return list(result.scalars().all())


async def 列出文章(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: 用户 | None,
    category: str | None,
    tag: str | None,
    search: str | None,
    sign_cover_url: bool = False,
) -> PaginatedResponse:
    """获取公开文章列表。"""
    query = 文章查询().where(构建博客可见文章条件(user))
    if category:
        query = query.where(文章.category.has(slug=category))
    if tag:
        query = query.where(文章.tags.any(标签.slug == tag))
    搜索条件 = 构建文章搜索条件(search, user)
    if 搜索条件 is not None:
        query = query.where(搜索条件)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(func.coalesce(文章.published_at, 文章.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[构建文章列表项响应(item, sign_cover_url=sign_cover_url) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 列出我的文章(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: 用户,
    category_filter: str = 全部文章分类筛选值,
) -> PaginatedResponse:
    """获取当前用户的文章列表。"""
    query = 文章查询().where(文章.author_id == user.id)
    query = query.where(文章.is_deleted.is_(False))
    if category_filter == 未分类文章分类筛选值:
        query = query.where(文章.category_id.is_(None))
    elif category_filter and category_filter != 全部文章分类筛选值:
        query = query.where(文章.category_id == category_filter)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(文章.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[文章列表项.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 列出我删除的文章(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    user: 用户,
    category_filter: str = 全部文章分类筛选值,
) -> PaginatedResponse:
    """获取当前用户回收站中的文章列表。"""
    query = 文章查询().where(
        文章.author_id == user.id,
        文章.is_deleted.is_(True),
    )
    if category_filter == 未分类文章分类筛选值:
        query = query.where(文章.category_id.is_(None))
    elif category_filter and category_filter != 全部文章分类筛选值:
        query = query.where(文章.category_id == category_filter)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(文章.deleted_at.desc(), 文章.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[文章列表项.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 按标识获取文章(db: AsyncSession, slug: str, user: 用户 | None) -> 文章:
    """按 slug 获取当前用户可访问的文章详情，并增加浏览量。"""
    result = await db.execute(
        文章查询().where(
            文章.slug == slug,
            文章.is_deleted.is_(False),
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not 用户可否阅读文章(article, user):
        if article.status == 文章状态.login_required:
            raise HTTPException(status_code=401, detail="该文章需要登录后查看")
        raise HTTPException(status_code=404, detail="文章不存在")
    article.view_count += 1
    await db.flush()
    return article


async def 获取相关文章(db: AsyncSession, slug: str, user: 用户 | None) -> 文章:
    """按 slug 获取文章，不增加浏览量。"""
    result = await db.execute(
        文章查询().where(
            文章.slug == slug,
            文章.is_deleted.is_(False),
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not 用户可否阅读文章(article, user):
        if article.status == 文章状态.login_required:
            raise HTTPException(status_code=401, detail="该文章需要登录后查看")
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


async def 按标识点赞文章(
    db: AsyncSession,
    slug: str,
    user: 用户 | None,
    request: Request,
    response: Response,
) -> 文章点赞信息:
    """按 slug 点赞文章，并基于匿名访客标识去重。"""
    article = await 获取相关文章(db, slug, user)
    visitor_id = 确保访客ID(request, response)
    changed = await 单次添加集合成员(f"like:article:{article.id}", visitor_id)
    if changed:
        article.like_count += 1
        await db.flush()
    return 文章点赞信息(like_count=article.like_count, changed=changed, liked=True)


async def 取消按标识点赞文章(
    db: AsyncSession,
    slug: str,
    user: 用户 | None,
    request: Request,
) -> 文章点赞信息:
    """按 slug 取消点赞文章。"""
    article = await 获取相关文章(db, slug, user)
    visitor_id = 获取访客ID(request)
    if not visitor_id:
        return 文章点赞信息(like_count=article.like_count, changed=False, liked=False)

    changed = await 移除集合成员(f"like:article:{article.id}", visitor_id)
    if changed:
        article.like_count = max(0, article.like_count - 1)
        await db.flush()
    return 文章点赞信息(like_count=article.like_count, changed=changed, liked=False)


async def 访客是否已点赞文章(article_id: UUID, request: Request) -> bool:
    """判断当前匿名访客是否已点赞文章。"""
    visitor_id = 获取访客ID(request)
    if not visitor_id:
        return False
    return await 包含集合成员(f"like:article:{article_id}", visitor_id)


async def 获取相关和随机文章(
    db: AsyncSession,
    slug: str,
    user: 用户 | None,
) -> tuple[文章 | None, 文章 | None, list[文章], list[文章]]:
    """获取上一篇、下一篇、相关文章和随机推荐文章。"""
    current = await 获取相关文章(db, slug, user)
    all_articles = await 列出全部文章元数据(db, user=user)
    sorted_articles = 排序文章用于导航(all_articles)

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

    scored: list[tuple[文章, float]] = []
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
