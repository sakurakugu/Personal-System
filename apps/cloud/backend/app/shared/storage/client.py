"""对象存储客户端与文件读写能力。"""

from __future__ import annotations

import io
from collections.abc import Iterable
from dataclasses import dataclass
import logging
from urllib.parse import quote
from uuid import UUID

from minio import Minio

from app.shared.kernel.config import settings
from app.utils.uuid import generate_uuid7

_minio_client: Minio | None = None
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObjectStream:
    """对象存储流式读取结果。"""

    chunks: Iterable[bytes]
    content_type: str
    content_length: int | None


class StorageBucketMissingError(RuntimeError):
    """对象存储桶不存在。"""


def _获取_minio_客户端() -> Minio:
    """获取 MinIO 客户端并确保存储桶存在。"""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        确保存储桶存在(_minio_client)
    return _minio_client


def 创建存储客户端() -> Minio:
    """创建 MinIO 客户端。"""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def 确保存储桶存在(client: Minio | None = None) -> None:
    """确保目标存储桶存在，不存在时自动创建。"""
    target_client = client or 创建存储客户端()
    if not target_client.bucket_exists(settings.MINIO_BUCKET):
        target_client.make_bucket(settings.MINIO_BUCKET)


def 检查存储健康() -> None:
    """检查 MinIO 服务与目标存储桶是否可用。"""
    client = 创建存储客户端()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        raise StorageBucketMissingError("存储桶不存在")


def 构建存储键(user_id: UUID, filename: str, *, directory: str = "") -> str:
    """按用户目录与业务子目录生成对象存储路径。"""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    object_id = generate_uuid7()
    normalized_directory = directory.strip("/")
    prefix = f"{user_id}/{normalized_directory}" if normalized_directory else str(user_id)
    return f"{prefix}/{object_id}.{ext}" if ext else f"{prefix}/{object_id}"


def 构建公开URL(storage_key: str) -> str:
    """构造文件公开访问地址。"""
    normalized_storage_key = quote(storage_key, safe="/")
    return f"/files/{normalized_storage_key}"


def upload_bytes(*, storage_key: str, content: bytes, content_type: str) -> None:
    """上传字节内容到对象存储。"""
    client = _获取_minio_客户端()
    client.put_object(
        settings.MINIO_BUCKET,
        storage_key,
        io.BytesIO(content),
        length=len(content),
        content_type=content_type,
    )


def 获取对象字节(storage_key: str) -> tuple[bytes, str]:
    """读取对象存储中的文件内容与媒体类型。"""
    client = _获取_minio_客户端()
    response = client.get_object(settings.MINIO_BUCKET, storage_key)

    try:
        content = response.read()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return content, content_type
    finally:
        response.close()
        response.release_conn()


def _解析内容长度(value: str | None) -> int | None:
    """解析响应头中的内容长度。"""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def 打开对象流(storage_key: str, *, chunk_size: int = 64 * 1024) -> ObjectStream:
    """以流式方式读取对象存储中的文件内容。"""
    client = _获取_minio_客户端()
    response = client.get_object(settings.MINIO_BUCKET, storage_key)
    content_type = response.headers.get("Content-Type", "application/octet-stream")
    content_length = _解析内容长度(response.headers.get("Content-Length"))

    def iterate_chunks() -> Iterable[bytes]:
        try:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return ObjectStream(
        chunks=iterate_chunks(),
        content_type=content_type,
        content_length=content_length,
    )


def 尽力删除对象(storage_key: str) -> None:
    """尽力删除单个对象。"""
    尽力删除多个对象([storage_key])


def 尽力删除多个对象(storage_keys: Iterable[str]) -> None:
    """尽力批量删除对象，失败时静默跳过。"""
    keys = [storage_key for storage_key in storage_keys if storage_key]
    if not keys:
        return

    try:
        client = _获取_minio_客户端()
        for storage_key in keys:
            client.remove_object(settings.MINIO_BUCKET, storage_key)
    except Exception:
        logger.warning("对象删除失败，已跳过清理，共 %s 个对象", len(keys), exc_info=True)
