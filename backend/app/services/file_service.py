"""文件管理服务。"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.user import User
from app.services.storage_service import (
    build_public_url,
    build_storage_key,
    remove_object_best_effort,
    upload_bytes,
)

最大上传字节数 = 10 * 1024 * 1024


async def list_files(db: AsyncSession, user: User) -> list[File]:
    """获取当前用户的文件列表。"""
    result = await db.execute(
        select(File).where(File.user_id == user.id).order_by(File.created_at.desc())
    )
    return list(result.scalars().all())


async def upload_file(db: AsyncSession, user: User, file: UploadFile) -> File:
    """上传文件并持久化元数据。"""
    content = await file.read()
    size = len(content)
    if size > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    filename = file.filename or ""
    storage_key = build_storage_key(user.id, filename)
    content_type = file.content_type or "application/octet-stream"
    upload_bytes(storage_key=storage_key, content=content, content_type=content_type)

    record = File(
        user_id=user.id,
        original_name=filename or "unknown",
        storage_key=storage_key,
        url=build_public_url(storage_key),
        size=size,
        mime_type=content_type,
    )
    db.add(record)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        remove_object_best_effort(storage_key)
        raise

    await db.refresh(record)
    return record


async def delete_file(db: AsyncSession, user: User, file_id: str) -> None:
    """删除文件记录，并在提交后清理对象存储。"""
    result = await db.execute(select(File).where(File.id == file_id, File.user_id == user.id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    storage_key = record.storage_key
    await db.delete(record)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    remove_object_best_effort(storage_key)
