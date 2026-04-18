"""文章分类与标签服务。"""

from __future__ import annotations

from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import Article, Category, Tag
from app.modules.articles.schemas import CategoryCreate, CategoryRead, TagCreate, TagRead
from app.modules.stats.service import invalidate_blog_stats_cache


async def list_categories(db: AsyncSession) -> list[CategoryRead]:
    """获取所有分类列表。"""
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return [
        CategoryRead(
            id=item.id,
            name=item.name,
            slug=item.slug,
            description=item.description,
            article_count=item.article_count or 0,
            created_at=item.created_at,
        )
        for item in categories
    ]


async def create_category(db: AsyncSession, body: CategoryCreate) -> Category:
    """创建新分类。"""
    category = Category(name=body.name, slug=slugify(body.name), description=body.description)
    db.add(category)
    await db.flush()
    await db.refresh(category)
    await invalidate_blog_stats_cache()
    return category


async def delete_category(db: AsyncSession, category_id: str) -> None:
    """删除分类。"""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    await db.execute(
        update(Article)
        .where(Article.category_id == category_id)
        .values(category_id=None)
    )
    await db.delete(category)
    await invalidate_blog_stats_cache()


async def list_tags(db: AsyncSession) -> list[TagRead]:
    """获取所有标签列表。"""
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [TagRead.model_validate(item) for item in tags]


async def create_tag(db: AsyncSession, body: TagCreate) -> Tag:
    """创建新标签。"""
    tag = Tag(name=body.name, slug=slugify(body.name))
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    await invalidate_blog_stats_cache()
    return tag


async def delete_tag(db: AsyncSession, tag_id: str) -> None:
    """删除标签。"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await invalidate_blog_stats_cache()
