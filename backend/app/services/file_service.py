"""文件管理服务。"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException, UploadFile
import pillow_avif  # noqa: F401
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
AVIF质量 = 60
默认图片文件名 = "image"
默认普通文件名 = "file"
图片扩展名 = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}
扩展名到媒体类型映射 = {
    ".avif": "image/avif",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".ico": "image/x-icon",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
    ".zip": "application/zip",
}


@dataclass(frozen=True)
class PreparedUpload:
    """规范化后的上传内容。"""

    original_name: str
    storage_name: str
    content: bytes
    content_type: str


def normalize_content_type(content_type: str) -> str:
    """规范化媒体类型字符串。"""
    normalized = content_type.strip().lower()
    if normalized == "image/jpg":
        return "image/jpeg"
    return normalized


def guess_extension(filename: str, content_type: str) -> str:
    """优先从文件名，其次从媒体类型推断扩展名。"""
    suffix = Path(filename).suffix.strip().lower()
    if suffix:
        return suffix

    normalized_content_type = normalize_content_type(content_type)
    for ext, mapped_content_type in 扩展名到媒体类型映射.items():
        if mapped_content_type == normalized_content_type:
            return ext
    return ""


def guess_content_type(content_type: str, filename: str) -> str:
    """优先使用上传声明的媒体类型，其次从扩展名推断。"""
    normalized_content_type = normalize_content_type(content_type)
    if normalized_content_type:
        return normalized_content_type

    return 扩展名到媒体类型映射.get(guess_extension(filename, normalized_content_type), "application/octet-stream")


def build_fallback_filename(filename: str, content_type: str) -> str:
    """为空文件名生成兜底名称。"""
    stripped_filename = filename.strip()
    if stripped_filename:
        return stripped_filename

    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    stem = 默认图片文件名 if normalized_content_type.startswith("image/") else 默认普通文件名
    return f"{stem}{ext}" if ext else stem


def build_target_filename(source_filename: str, target_ext: str) -> str:
    """基于原始名称生成目标格式文件名。"""
    fallback_filename = build_fallback_filename(source_filename, "")
    stem = Path(fallback_filename).stem.strip()
    if not stem or stem == ".":
        stem = 默认图片文件名
    return f"{stem}{target_ext}"


def is_image_upload(filename: str, content_type: str) -> bool:
    """根据扩展名与媒体类型判断是否为图片。"""
    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    return normalized_content_type.startswith("image/") or ext in 图片扩展名


def is_svg_upload(filename: str, content_type: str) -> bool:
    """判断是否为 SVG 矢量图。"""
    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    return ext == ".svg" or normalized_content_type == "image/svg+xml"


def is_avif_upload(filename: str, content_type: str) -> bool:
    """判断是否已经是 AVIF。"""
    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    return ext == ".avif" or normalized_content_type == "image/avif"


def is_animated_image(image: Image.Image) -> bool:
    """判断图片是否包含多帧动画。"""
    return bool(getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1)


def convert_image_to_avif(content: bytes) -> bytes:
    """将静态位图转换为 AVIF。"""
    with Image.open(io.BytesIO(content)) as image:
        normalized_image = ImageOps.exif_transpose(image)

        if (
            normalized_image.mode in {"RGBA", "LA"}
            or (normalized_image.mode == "P" and "transparency" in normalized_image.info)
        ):
            normalized_image = normalized_image.convert("RGBA")
        else:
            normalized_image = normalized_image.convert("RGB")

        output = io.BytesIO()
        normalized_image.save(output, format="AVIF", quality=AVIF质量)
        return output.getvalue()


def prepare_upload_payload(filename: str, content_type: str, content: bytes) -> PreparedUpload:
    """将上传内容规范化为最终存储格式。"""
    resolved_content_type = guess_content_type(content_type, filename)
    resolved_filename = build_fallback_filename(filename, resolved_content_type)

    if not is_image_upload(resolved_filename, resolved_content_type):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    if is_svg_upload(resolved_filename, resolved_content_type) or is_avif_upload(
        resolved_filename, resolved_content_type
    ):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    try:
        with Image.open(io.BytesIO(content)) as image:
            if is_animated_image(image):
                return PreparedUpload(
                    original_name=resolved_filename,
                    storage_name=resolved_filename,
                    content=content,
                    content_type=resolved_content_type,
                )
    except (UnidentifiedImageError, OSError, ValueError):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    converted_content = convert_image_to_avif(content)
    return PreparedUpload(
        original_name=resolved_filename,
        storage_name=build_target_filename(resolved_filename, ".avif"),
        content=converted_content,
        content_type="image/avif",
    )


async def list_files(db: AsyncSession, user: User) -> list[File]:
    """获取当前用户的文件列表。"""
    result = await db.execute(
        select(File).where(File.user_id == user.id).order_by(File.created_at.desc())
    )
    records = list(result.scalars().all())
    for record in records:
        record.url = build_public_url(record.storage_key)
    return records


async def upload_file(db: AsyncSession, user: User, file: UploadFile) -> File:
    """上传文件并持久化元数据。"""
    content = await file.read()
    if len(content) > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    prepared_upload = prepare_upload_payload(
        filename=file.filename or "",
        content_type=file.content_type or "",
        content=content,
    )
    storage_key = build_storage_key(user.id, prepared_upload.storage_name)
    upload_bytes(
        storage_key=storage_key,
        content=prepared_upload.content,
        content_type=prepared_upload.content_type,
    )

    record = File(
        user_id=user.id,
        original_name=prepared_upload.original_name,
        storage_key=storage_key,
        url=build_public_url(storage_key),
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
    record.url = build_public_url(record.storage_key)
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
