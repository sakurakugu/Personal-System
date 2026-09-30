"""博客发布快照与管理服务。"""

import logging
import math

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import 文章, 博客发布
from app.modules.articles.queries import 获取我的文章
from app.modules.articles.schemas import 分类信息, 标签信息, 博客发布请求
from app.modules.articles.workflow import 文章查询
from app.modules.articles.content import utcnow
from app.modules.feed.service import 同步文章Feed条目, 清除Feed首页缓存
from app.modules.stats.service import 清除博客统计缓存
from app.modules.users.models import 用户

logger = logging.getLogger(__name__)


async def 提交博客发布事务(db: AsyncSession) -> None:
    """提交快照及同一事务的操作日志，再刷新公开数据缓存。"""
    await db.commit()
    await 清除Feed首页缓存()
    await 清除博客统计缓存()
    logger.info("博客发布事务已提交并刷新缓存")


def 构建博客管理项(article: 文章) -> dict:
    """同时返回文章信息和上次发布信息。"""
    blog = article.blog
    return {
        "id": str(article.id),
        "title": article.title,
        "word_count": article.word_count,
        "revision": article.revision,
        "has_unpublished_changes": article.has_unpublished_changes,
        "publication": {
            "title": blog.title,
            "word_count": blog.word_count,
            "slug": blog.slug,
            "visibility": blog.status,
            "is_published": blog.is_published,
            "version": blog.version,
            "published_at": blog.published_at.isoformat(),
            "updated_at": blog.last_edited_at.isoformat(),
            "view_count": blog.view_count,
            "like_count": blog.like_count,
        }
        if blog
        else None,
    }


async def 列出博客管理(
    db: AsyncSession, user: 用户, page: int, page_size: int, search: str | None, state: str
) -> dict:
    """分页管理全部文章及发布状态。"""
    query = 文章查询().where(文章.author_id == user.id, 文章.is_deleted.is_(False))
    if search and search.strip():
        query = query.where(文章.title.ilike(f"%{search.strip()}%"))
    if state == "published":
        query = query.where(文章.blog.has(博客发布.is_published.is_(True)))
    elif state == "unpublished":
        query = query.where(~文章.blog.has(博客发布.is_published.is_(True)))
    elif state == "changed":
        query = query.where(文章.blog.has(博客发布.source_revision != 文章.revision))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    articles = (
        (
            await db.execute(
                query.order_by(文章.last_edited_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return {
        "items": [构建博客管理项(article) for article in articles],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size),
    }


async def 发布博客(db: AsyncSession, article_id: str, body: 博客发布请求, user: 用户) -> dict:
    """将指定文章完整复制到发布快照，保留链接与互动统计。"""
    await db.execute(select(文章.id).where(文章.id == article_id).with_for_update())
    article = await 获取我的文章(db, article_id, user)
    if article.revision != body.expected_revision:
        raise HTTPException(status_code=409, detail="文章已更新，请刷新后再发布")
    if not article.title.strip() or not article.content.strip():
        raise HTTPException(status_code=400, detail="发布前请填写标题和正文")
    now = utcnow()
    blog = article.blog
    if blog is None:
        blog = 博客发布(
            id=article.id,
            author_id=article.author_id,
            slug=article.slug,
            published_at=now,
            created_at=article.created_at,
            version=0,
            view_count=0,
            like_count=0,
        )
        article.blog = blog
    for field in ("title", "content", "excerpt", "cover_url", "word_count"):
        setattr(blog, field, getattr(article, field))
    blog.category_snapshot = (
        分类信息.model_validate(article.category).model_dump(mode="json")
        if article.category
        else None
    )
    blog.tags_snapshot = [
        标签信息.model_validate(tag).model_dump(mode="json") for tag in article.tags
    ]
    blog.source_revision = article.revision
    blog.version += 1
    blog.status = body.visibility
    blog.is_published = True
    blog.last_edited_at = now
    blog.updated_at = now
    await db.flush()
    await 同步文章Feed条目(db, blog)
    logger.info(
        "博客快照已写入事务，文章=%s，文章版本=%s，发布版本=%s，可见性=%s",
        article.id,
        article.revision,
        blog.version,
        blog.status,
    )
    return 构建博客管理项(article)


async def 修改博客发布状态(
    db: AsyncSession, article_id: str, user: 用户, *, visibility: str | None = None
) -> dict:
    """调整可见性或撤下，保留已发布内容。"""
    await db.execute(select(文章.id).where(文章.id == article_id).with_for_update())
    article = await 获取我的文章(db, article_id, user)
    blog = article.blog
    if blog is None:
        raise HTTPException(status_code=404, detail="文章尚未发布到博客")
    if visibility is None:
        blog.is_published = False
    else:
        blog.status = visibility
    await db.flush()
    await 同步文章Feed条目(db, blog)
    logger.info(
        "博客发布状态已写入事务，文章=%s，已发布=%s，可见性=%s",
        article.id,
        blog.is_published,
        blog.status,
    )
    return 构建博客管理项(article)
