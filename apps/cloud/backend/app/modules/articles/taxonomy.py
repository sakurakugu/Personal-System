"""文章分类与标签服务。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from slugify import slugify
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import UTC时间戳起点
from app.modules.articles.models import 文章, 文章标签, 分类, 标签
from app.modules.articles.permissions import 构建博客可见文章条件
from app.modules.articles.queries import 全部文章分类筛选值, 未分类文章分类筛选值
from app.modules.articles.schemas import 分类创建, 分类信息, 标签创建, 标签信息
from app.modules.stats.service import 清除博客统计缓存
from app.modules.users.models import 用户
from app.utils.uuid import generate_uuid7

保留分类标识集合 = {全部文章分类筛选值, 未分类文章分类筛选值}


def _截断标识(slug: str, max_length: int) -> str:
    """按字段长度截断 slug，并去掉末尾连接符。"""
    return slug[:max_length].rstrip("-") or slug[:max_length]


def _构建基础标识(name: str, *, fallback_prefix: str, max_length: int) -> str:
    """根据名称生成基础 slug，无法转写时使用稳定前缀。"""
    generated_slug = slugify(name.strip())
    if generated_slug:
        return _截断标识(generated_slug, max_length)
    return f"{fallback_prefix}-{generate_uuid7().hex[:8]}"


async def _构建可用分类标识(db: AsyncSession, name: str) -> str:
    """生成不会与现有分类冲突的 slug。"""
    max_length = 120
    suffix_length = 9
    base_slug = _构建基础标识(name, fallback_prefix="category", max_length=max_length)
    if base_slug in 保留分类标识集合:
        raise HTTPException(status_code=400, detail="分类名称会生成系统保留标识，请换一个名称")
    existing = await db.execute(select(分类.id).where(分类.slug == base_slug))
    if existing.scalar_one_or_none() is None:
        return base_slug
    return f"{_截断标识(base_slug, max_length - suffix_length)}-{generate_uuid7().hex[:8]}"


async def _构建可用标签标识(db: AsyncSession, name: str) -> str:
    """生成不会与现有标签冲突的 slug。"""
    max_length = 80
    suffix_length = 9
    base_slug = _构建基础标识(name, fallback_prefix="tag", max_length=max_length)
    existing = await db.execute(select(标签.id).where(标签.slug == base_slug))
    if existing.scalar_one_or_none() is None:
        return base_slug
    return f"{_截断标识(base_slug, max_length - suffix_length)}-{generate_uuid7().hex[:8]}"


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


async def 列出可见分类(db: AsyncSession, user: 用户 | None) -> tuple[list[分类信息], datetime]:
    """获取当前访问者可在博客看到的分类，并按可见文章数计数。"""
    article_count = func.count(文章.id).label("article_count")
    last_article_updated_at = func.max(文章.updated_at).label("last_article_updated_at")
    result = await db.execute(
        select(分类, article_count, last_article_updated_at)
        .join(文章, 文章.category_id == 分类.id)
        .where(构建博客可见文章条件(user))
        .group_by(分类.id)
        .order_by(分类.name)
    )
    rows = result.all()
    categories = [
        分类信息(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            article_count=int(count or 0),
            created_at=category.created_at,
        )
        for category, count, _last_article_updated_at in rows
    ]
    last_modified = max(
        (
            value
            for category, _count, article_updated_at in rows
            for value in (category.created_at, article_updated_at)
            if value is not None
        ),
        default=UTC时间戳起点,
    )
    return categories, last_modified


async def 列出我的有文章分类(db: AsyncSession, user_id: UUID, *, is_deleted: bool = False) -> list[分类信息]:
    """获取当前用户有文章的分类列表，并按当前用户文章数计数。"""
    article_count = func.count(文章.id).label("article_count")
    result = await db.execute(
        select(分类, article_count)
        .join(文章, 文章.category_id == 分类.id)
        .where(
            文章.author_id == user_id,
            文章.is_deleted.is_(is_deleted),
        )
        .group_by(分类.id)
        .order_by(分类.name)
    )
    return [
        分类信息(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            article_count=int(count or 0),
            created_at=category.created_at,
        )
        for category, count in result.all()
    ]


async def 创建分类(db: AsyncSession, body: 分类创建) -> 分类:
    """创建新分类。"""
    existing = await db.execute(select(分类.id).where(分类.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="分类已存在")
    category = 分类(
        name=body.name,
        slug=await _构建可用分类标识(db, body.name),
        description=body.description,
    )
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


async def 列出可见标签(db: AsyncSession, user: 用户 | None) -> tuple[list[标签信息], datetime]:
    """获取当前访问者可在博客看到的标签。"""
    last_article_updated_at = func.max(文章.updated_at).label("last_article_updated_at")
    result = await db.execute(
        select(标签, last_article_updated_at)
        .join(文章标签, 文章标签.tag_id == 标签.id)
        .join(文章, 文章.id == 文章标签.article_id)
        .where(构建博客可见文章条件(user))
        .group_by(标签.id)
        .order_by(标签.name)
    )
    rows = result.all()
    tags = [标签信息.model_validate(tag) for tag, _last_article_updated_at in rows]
    last_modified = max(
        (
            value
            for tag, article_updated_at in rows
            for value in (tag.created_at, article_updated_at)
            if value is not None
        ),
        default=UTC时间戳起点,
    )
    return tags, last_modified


async def 创建标签(db: AsyncSession, body: 标签创建) -> 标签:
    """创建新标签。"""
    existing = await db.execute(select(标签.id).where(标签.name == body.name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="标签已存在")
    tag = 标签(name=body.name, slug=await _构建可用标签标识(db, body.name))
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
