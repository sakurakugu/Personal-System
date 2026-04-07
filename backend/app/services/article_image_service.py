"""文章图片服务。"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import ArticleImage
from app.models.user import User
from app.schemas.article import ArticleImageRead
from app.services.article_service import ensure_article_write_permission, get_article_or_404
from app.services.file_service import (
    is_image_upload,
    prepare_upload_payload,
    最大上传字节数,
)
from app.services.storage_service import (
    build_public_url,
    build_storage_key,
    remove_object_best_effort,
    upload_bytes,
)


def build_article_image_directory(article_id: str) -> str:
    """构造文章图片的对象存储目录。"""
    return f"articles/{article_id}"


async def upload_article_image(
    db: AsyncSession,
    user: User,
    article_id: str,
    file: UploadFile,
) -> ArticleImageRead:
    """上传文章图片并返回访问地址。"""
    article = await get_article_or_404(db, article_id)
    ensure_article_write_permission(article, user)

    content = await file.read()
    if len(content) > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    original_filename = file.filename or ""
    original_content_type = file.content_type or ""
    if not is_image_upload(original_filename, original_content_type):
        raise HTTPException(status_code=400, detail="文章图片只允许上传图片文件")

    prepared_upload = prepare_upload_payload(
        filename=original_filename,
        content_type=original_content_type,
        content=content,
        compress_static_images=True,
    )
    storage_key = build_storage_key(
        user.id,
        prepared_upload.storage_name,
        directory=build_article_image_directory(article_id),
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
        remove_object_best_effort(storage_key)
        raise

    await db.refresh(record)
    return ArticleImageRead(
        id=record.id,
        original_name=record.original_name,
        url=build_public_url(record.storage_key),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
    )
