"""文章 CRUD 编排。"""

from __future__ import annotations

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.content import 计算字数, 从Markdown首行提取标题, utcnow
from app.modules.feed.models import FeedItemType
from app.modules.feed.service import 删除Feed条目, 清除Feed首页缓存, 同步文章Feed条目
from app.modules.articles.models import 文章, 文章状态, 文章标签, 分类
from app.modules.articles.permissions import 确保文章写入权限
from app.modules.articles.queries import (
    获取已删除文章或404,
    获取文章或404,
    列出文章图片存储键,
)
from app.modules.articles.schemas import 文章创建, 文章草稿创建, 文章更新
from app.modules.articles.workflow import (
    应用文章状态,
    应用文章删除状态,
    构建可用文章标识,
    解析文章状态,
    恢复文章删除状态,
    刷新文章最后编辑时间,
)
from app.modules.stats.service import 清除博客统计缓存
from app.shared.storage.client import 尽力删除多个对象
from app.utils.uuid import generate_uuid7
from app.modules.users.models import 用户


def _解析文章标题(title: str | None, content: str | None) -> str:
    """优先使用显式标题，否则退回到正文首个非空行。"""
    normalized_title = (title or "").strip()
    if normalized_title:
        return normalized_title
    return 从Markdown首行提取标题(content)


async def 替换文章标签(db: AsyncSession, article_id: str, tag_ids: list[str]) -> None:
    """替换文章标签关联。"""
    await db.execute(delete(文章标签).where(文章标签.article_id == article_id))
    for tag_id in tag_ids:
        db.add(文章标签(article_id=article_id, tag_id=tag_id))


async def 创建文章(db: AsyncSession, body: 文章创建, user: 用户) -> 文章:
    """创建文章。"""
    status = 解析文章状态(body.status)
    current_time = utcnow()
    article_id = generate_uuid7()
    resolved_title = _解析文章标题(body.title, body.content)
    article = 文章(
        id=article_id,
        title=resolved_title,
        slug=await 构建可用文章标识(db, resolved_title, article_id, now=current_time),
        content=body.content,
        excerpt=body.excerpt,
        cover_url=body.cover_url,
        status=status,
        word_count=计算字数(body.content),
        author_id=user.id,
        category_id=body.category_id,
        last_edited_at=current_time,
    )
    应用文章状态(article, status, now=current_time)
    db.add(article)
    await db.flush()

    if body.tag_ids:
        await 替换文章标签(db, str(article.id), [str(tag_id) for tag_id in body.tag_ids])
        await db.flush()

    if body.category_id is not None:
        await db.execute(
            update(分类)
            .where(分类.id == body.category_id)
            .values(article_count=分类.article_count + 1)
        )

    await 同步文章Feed条目(db, article)
    await db.flush()

    await 清除Feed首页缓存()
    await 清除博客统计缓存()
    return await 获取文章或404(db, str(article.id))


async def 创建文章草稿(db: AsyncSession, body: 文章草稿创建 | None, user: 用户) -> 文章:
    """创建文章草稿占位。"""
    payload = body or 文章草稿创建()
    current_time = utcnow()
    article_id = generate_uuid7()
    resolved_title = _解析文章标题(payload.title, payload.content)
    article = 文章(
        id=article_id,
        title=resolved_title,
        slug=await 构建可用文章标识(db, resolved_title, article_id, now=current_time),
        content=payload.content or "",
        excerpt=payload.excerpt,
        cover_url=payload.cover_url,
        status=文章状态.private,
        word_count=计算字数(payload.content or ""),
        author_id=user.id,
        category_id=payload.category_id,
        last_edited_at=current_time,
    )
    应用文章状态(article, 文章状态.private, now=current_time)
    db.add(article)
    await db.flush()

    if payload.tag_ids:
        await 替换文章标签(db, str(article.id), [str(tag_id) for tag_id in payload.tag_ids])
        await db.flush()

    return await 获取文章或404(db, str(article.id))


async def 更新文章(db: AsyncSession, article_id: str, body: 文章更新, user: 用户) -> 文章:
    """更新文章。"""
    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)

    data = body.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    status_value = data.pop("status", None)
    current_time = utcnow()
    old_category_id = article.category_id
    incoming_content = data.get("content", article.content)
    title_was_provided = "title" in data

    if title_was_provided:
        data["title"] = _解析文章标题(data.get("title"), incoming_content)

    for key, value in data.items():
        setattr(article, key, value)

    if not title_was_provided and not article.title.strip():
        article.title = 从Markdown首行提取标题(article.content)

    if "content" in data:
        article.word_count = 计算字数(article.content)

    if article.title and article.slug.startswith("draft-"):
        article.slug = await 构建可用文章标识(
            db,
            article.title,
            article.id,
            current_article_id=article.id,
            now=current_time,
        )

    if status_value is not None:
        应用文章状态(article, 解析文章状态(status_value), now=current_time)

    if tag_ids is not None:
        await 替换文章标签(db, article_id, [str(tag_id) for tag_id in tag_ids])

    new_category_id = article.category_id
    if "category_id" in data and old_category_id != new_category_id:
        if old_category_id is not None:
            await db.execute(
                update(分类)
                .where(分类.id == old_category_id)
                .values(article_count=分类.article_count - 1)
            )
        if new_category_id is not None:
            await db.execute(
                update(分类)
                .where(分类.id == new_category_id)
                .values(article_count=分类.article_count + 1)
            )

    刷新文章最后编辑时间(article, now=current_time)
    await 同步文章Feed条目(db, article)
    await db.flush()

    await 清除Feed首页缓存()
    await 清除博客统计缓存()
    return await 获取文章或404(db, article_id)


async def 删除文章(db: AsyncSession, article_id: str, user: 用户, *, permanent: bool) -> None:
    """删除文章。"""
    if permanent:
        article = await 获取已删除文章或404(db, article_id)
        确保文章写入权限(article, user)
        image_storage_keys = await 列出文章图片存储键(db, article.id)
        await 删除Feed条目(db, FeedItemType.article, article.id)
        await db.delete(article)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await 清除Feed首页缓存()
        await 清除博客统计缓存()
        尽力删除多个对象(image_storage_keys)
        return

    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)
    category_id = article.category_id
    应用文章删除状态(article, now=utcnow())
    await 删除Feed条目(db, FeedItemType.article, article.id)

    if category_id is not None:
        await db.execute(
            update(分类)
            .where(分类.id == category_id)
            .values(article_count=分类.article_count - 1)
        )

    await db.flush()
    await 清除Feed首页缓存()
    await 清除博客统计缓存()


async def 恢复文章(db: AsyncSession, article_id: str, user: 用户) -> 文章:
    """从回收站恢复文章。"""
    article = await 获取已删除文章或404(db, article_id)
    确保文章写入权限(article, user)
    category_id = article.category_id
    恢复文章删除状态(article)

    if category_id is not None:
        await db.execute(
            update(分类)
            .where(分类.id == category_id)
            .values(article_count=分类.article_count + 1)
        )

    await 同步文章Feed条目(db, article)
    await db.flush()
    await 清除Feed首页缓存()
    await 清除博客统计缓存()
    return await 获取文章或404(db, article_id)
