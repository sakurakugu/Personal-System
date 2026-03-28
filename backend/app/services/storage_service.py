"""MinIO 对象存储服务。"""

from __future__ import annotations

import io
from collections.abc import Iterable
from uuid import UUID

from minio import Minio

from app.core.config import settings
from app.utils.uuid import generate_uuid7

_minio_client: Minio | None = None


def _get_minio_client() -> Minio:
    """获取 MinIO 客户端并确保存储桶存在。"""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
            _minio_client.make_bucket(settings.MINIO_BUCKET)
    return _minio_client


def build_storage_key(user_id: UUID, filename: str) -> str:
    """按用户目录生成对象存储路径。"""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    object_id = generate_uuid7()
    return f"{user_id}/{object_id}.{ext}" if ext else f"{user_id}/{object_id}"


def build_public_url(storage_key: str) -> str:
    """构造文件公开访问地址。"""
    return f"{settings.MINIO_PUBLIC_URL}/{storage_key}"


def upload_bytes(*, storage_key: str, content: bytes, content_type: str) -> None:
    """上传字节内容到对象存储。"""
    client = _get_minio_client()
    client.put_object(
        settings.MINIO_BUCKET,
        storage_key,
        io.BytesIO(content),
        length=len(content),
        content_type=content_type,
    )


def remove_object_best_effort(storage_key: str) -> None:
    """尽力删除单个对象。"""
    remove_objects_best_effort([storage_key])


def remove_objects_best_effort(storage_keys: Iterable[str]) -> None:
    """尽力批量删除对象，失败时静默跳过。"""
    keys = [storage_key for storage_key in storage_keys if storage_key]
    if not keys:
        return

    try:
        client = _get_minio_client()
        for storage_key in keys:
            client.remove_object(settings.MINIO_BUCKET, storage_key)
    except Exception:
        pass
