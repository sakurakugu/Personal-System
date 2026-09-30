"""文章图片服务。"""

from __future__ import annotations

import logging

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.articles.models import 文章, 文章图片
from app.modules.articles.permissions import 确保文章写入权限
from app.modules.articles.queries import 获取文章或404
from app.modules.articles.schemas import 文章图片信息
from app.modules.files.operations import 最大上传字节数
from app.modules.files.upload_preparation import 是否为图片上传, 准备上传载荷
from app.shared.storage.client import (
    构建公开URL,
    构建存储键,
    尽力删除对象,
    upload_bytes,
)
from app.shared.storage.file_url import 构建签名文件URL, 收集托管文件存储键

logger = logging.getLogger(__name__)


def 构建文章图片目录(article_id: str) -> str:
    """构造文章图片的对象存储目录。"""
    return f"articles/{article_id}"


def 构建文章图片读取(record: 文章图片, *, used_by_publication: bool = False) -> 文章图片信息:
    """构造文章图片响应。"""
    thumbnail_url = None
    if record.mime_type.startswith("image/") and record.mime_type != "image/svg+xml":
        thumbnail_url = 构建签名文件URL(
            record.storage_key,
            query_params={
                "thumbnail_width": 144,
                "thumbnail_height": 144,
            },
        )

    return 文章图片信息(
        id=record.id,
        original_name=record.original_name,
        url=构建公开URL(record.storage_key),
        preview_url=构建签名文件URL(record.storage_key),
        thumbnail_url=thumbnail_url,
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        used_by_publication=used_by_publication,
    )


async def 列出文章图片(
    db: AsyncSession,
    user: 用户,
    article_id: str,
) -> list[文章图片信息]:
    """获取当前文章的全部图片。"""
    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)

    result = await db.execute(
        select(文章图片)
        .where(文章图片.article_id == article.id)
        .order_by(文章图片.created_at.desc())
    )
    blog = article.blog
    publication_keys = 收集托管文件存储键(blog.content, blog.cover_url) if blog else set()
    return [构建文章图片读取(record, used_by_publication=record.storage_key in publication_keys)
            for record in result.scalars().all()]


async def 删除文章图片(db: AsyncSession, user: 用户, article_id: str, image_id: str) -> None:
    """仅删除文章与发布快照都未引用的图片。"""
    await db.execute(select(文章.id).where(文章.id == article_id).with_for_update())
    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)
    result = await db.execute(select(文章图片).where(文章图片.id == image_id, 文章图片.article_id == article.id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    referenced = 收集托管文件存储键(article.content, article.cover_url)
    if article.blog:
        referenced |= 收集托管文件存储键(article.blog.content, article.blog.cover_url)
    if record.storage_key in referenced:
        raise HTTPException(status_code=409, detail="图片仍被文章或发布版本引用，不能删除")
    key = record.storage_key
    await db.delete(record)
    await db.commit()
    尽力删除对象(key)
    logger.info("已删除未使用文章图片，文章=%s，图片=%s", article_id, image_id)


async def 上传文章图片(
    db: AsyncSession,
    user: 用户,
    article_id: str,
    file: UploadFile,
) -> 文章图片信息:
    """上传文章图片并返回访问地址。"""
    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)

    content = await file.read()
    if len(content) > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    original_filename = file.filename or ""
    original_content_type = file.content_type or ""
    if not 是否为图片上传(original_filename, original_content_type):
        raise HTTPException(status_code=400, detail="文章图片只允许上传图片文件")

    prepared_upload = 准备上传载荷(
        filename=original_filename,
        content_type=original_content_type,
        content=content,
        compress_static_images=True,
    )
    storage_key = 构建存储键(
        user.id,
        prepared_upload.storage_name,
        directory=构建文章图片目录(article_id),
    )
    upload_bytes(
        storage_key=storage_key,
        content=prepared_upload.content,
        content_type=prepared_upload.content_type,
    )

    record = 文章图片(
        article_id=article.id,
        original_name=prepared_upload.original_name,
        storage_key=storage_key,
        size=len(prepared_upload.content),
        mime_type=prepared_upload.content_type,
    )
    db.add(record)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        尽力删除对象(storage_key)
        raise

    await db.refresh(record)
    return 构建文章图片读取(record)
