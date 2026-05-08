"""文章图片服务。"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.articles.models import ArticleImage
from app.modules.articles.permissions import 确保文章写入权限
from app.modules.articles.queries import 获取文章或404
from app.modules.articles.schemas import ArticleImageRead
from app.modules.files.operations import 最大上传字节数
from app.modules.files.upload_preparation import 是否为图片上传, 准备上传载荷
from app.shared.storage.client import (
    构建公开URL,
    构建存储键,
    尽力删除对象,
    upload_bytes,
)
from app.shared.storage.file_url import 构建签名文件URL


def 构建文章图片目录(article_id: str) -> str:
    """构造文章图片的对象存储目录。"""
    return f"articles/{article_id}"


def 构建文章图片读取(record: ArticleImage) -> ArticleImageRead:
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

    return ArticleImageRead(
        id=record.id,
        original_name=record.original_name,
        url=构建公开URL(record.storage_key),
        preview_url=构建签名文件URL(record.storage_key),
        thumbnail_url=thumbnail_url,
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
    )


async def 列出文章图片(
    db: AsyncSession,
    user: User,
    article_id: str,
) -> list[ArticleImageRead]:
    """获取当前文章的全部图片。"""
    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)

    result = await db.execute(
        select(ArticleImage)
        .where(ArticleImage.article_id == article.id)
        .order_by(ArticleImage.created_at.desc())
    )
    return [构建文章图片读取(record) for record in result.scalars().all()]


async def 上传文章图片(
    db: AsyncSession,
    user: User,
    article_id: str,
    file: UploadFile,
) -> ArticleImageRead:
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

    record = ArticleImage(
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
