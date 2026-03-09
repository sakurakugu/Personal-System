"""使用 MinIO 的文件上传路由。"""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import File, User
from app.schemas.schemas import FileRead
from app.utils.uuid import generate_uuid7

router = APIRouter(prefix="/files", tags=["files"])

# 懒加载 MinIO 客户端
_minio_client = None


def _get_minio():
    global _minio_client
    if _minio_client is None:
        from minio import Minio
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
            _minio_client.make_bucket(settings.MINIO_BUCKET)
    return _minio_client


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    size = len(content)
    if size > 10 * 1024 * 1024:  # 10 MB max
        raise HTTPException(status_code=413, detail="File too large (10MB max)")

    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    storage_key = f"{user.id}/{generate_uuid7()}.{ext}" if ext else f"{user.id}/{generate_uuid7()}"

    client = _get_minio()
    client.put_object(
        settings.MINIO_BUCKET,
        storage_key,
        io.BytesIO(content),
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )

    url = f"{settings.MINIO_PUBLIC_URL}/{storage_key}"
    record = File(
        user_id=user.id,
        original_name=filename or "unknown",
        storage_key=storage_key,
        url=url,
        size=size,
        mime_type=file.content_type or "application/octet-stream",
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


@router.get("", response_model=list[FileRead])
async def list_files(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(File).where(File.user_id == user.id).order_by(File.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(File).where(File.id == file_id, File.user_id == user.id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        client = _get_minio()
        client.remove_object(settings.MINIO_BUCKET, record.storage_key)
    except Exception:
        pass  # best-effort cleanup
    await db.delete(record)
