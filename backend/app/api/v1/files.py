"""使用 MinIO 的文件上传路由。

此模块提供文件管理接口，包括：
- 文件上传（保存到 MinIO 对象存储）
- 文件列表查询
- 文件删除

文件上传限制：最大 10MB
"""

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

# 创建路由器，前缀为 /files，标签为 files
router = APIRouter(prefix="/files", tags=["files"])

# 懒加载 MinIO 客户端（首次使用时初始化）
_minio_client = None


def _get_minio():
    """
    获取 MinIO 客户端实例（懒加载）。

    首次调用时初始化 MinIO 客户端，并确保存储桶存在。

    Returns:
        Minio: MinIO 客户端实例
    """
    global _minio_client
    if _minio_client is None:
        from minio import Minio
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        # 如果存储桶不存在则创建
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
            _minio_client.make_bucket(settings.MINIO_BUCKET)
    return _minio_client


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件到 MinIO 对象存储。

    文件大小限制为 10MB，上传后保存文件元数据到数据库。

    Args:
        file: 上传的文件
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        FileRead: 文件信息（包括访问 URL）

    Raises:
        HTTPException: 413 - 文件过大（最大 10MB）
    """
    content = await file.read()
    size = len(content)
    if size > 10 * 1024 * 1024:  # 10 MB max
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    # 生成存储路径：用户ID/UUID.扩展名
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    storage_key = f"{user.id}/{generate_uuid7()}.{ext}" if ext else f"{user.id}/{generate_uuid7()}"

    # 上传文件到 MinIO
    client = _get_minio()
    client.put_object(
        settings.MINIO_BUCKET,
        storage_key,
        io.BytesIO(content),
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )

    # 构建文件访问 URL
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
    """
    获取当前用户的文件列表。

    按创建时间倒序排列。

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        list[FileRead]: 文件列表
    """
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
    """
    删除文件。

    从数据库和 MinIO 存储桶中同时删除文件。

    Args:
        file_id: 文件 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 文件不存在
    """
    result = await db.execute(select(File).where(File.id == file_id, File.user_id == user.id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        # 从 MinIO 删除文件（best-effort，失败不报错）
        client = _get_minio()
        client.remove_object(settings.MINIO_BUCKET, record.storage_key)
    except Exception:
        pass  # best-effort cleanup
    await db.delete(record)
