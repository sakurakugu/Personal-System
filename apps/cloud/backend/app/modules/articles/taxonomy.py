"""文章分类与标签服务。"""

from __future__ import annotations

from fastapi import HTTPException
from slugify import slugify
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import 文章, 分类, 标签
from app.modules.articles.schemas import 分类创建, 分类信息, 标签创建, 标签信息
from app.modules.stats.service import 清除博客统计缓存


async def 列出分类(db: AsyncSession) -> list[分类信息]:
    """获取所有分类列表。"""
    result = await db.execute(select(分类).order_by(分类.name))
    categories = result.scalars().all()
    return [
        分类信息(
            id=item.id,
            name=item.name,
            slug=item.slug,
            description=item.description,
            article_count=item.article_count or 0,
            created_at=item.created_at,
        )
        for item in categories
    ]


async def 创建分类(db: AsyncSession, body: 分类创建) -> 分类:
    """创建新分类。"""
    category = 分类(name=body.name, slug=slugify(body.name), description=body.description)
    db.add(category)
    await db.flush()
    await db.refresh(category)
    await 清除博客统计缓存()
    return category


async def 删除分类(db: AsyncSession, category_id: str) -> None:
    """删除分类。"""
    result = await db.execute(select(分类).where(分类.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    await db.execute(
        update(文章)
        .where(文章.category_id == category_id)
        .values(category_id=None)
    )
    await db.delete(category)
    await 清除博客统计缓存()


async def 列出标签(db: AsyncSession) -> list[标签信息]:
    """获取所有标签列表。"""
    result = await db.execute(select(标签).order_by(标签.name))
    tags = result.scalars().all()
    return [标签信息.model_validate(item) for item in tags]


async def 创建标签(db: AsyncSession, body: 标签创建) -> 标签:
    """创建新标签。"""
    tag = 标签(name=body.name, slug=slugify(body.name))
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    await 清除博客统计缓存()
    return tag


async def 删除标签(db: AsyncSession, tag_id: str) -> None:
    """删除标签。"""
    result = await db.execute(select(标签).where(标签.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
    await 清除博客统计缓存()
