"""文件上传预处理。"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError
import pillow_avif  # noqa: F401

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


def 规范化内容类型(content_type: str) -> str:
    """规范化媒体类型字符串。"""
    normalized = content_type.strip().lower()
    if normalized == "image/jpg":
        return "image/jpeg"
    return normalized


def 推断扩展名(filename: str, content_type: str) -> str:
    """优先从文件名，其次从媒体类型推断扩展名。"""
    suffix = Path(filename).suffix.strip().lower()
    if suffix:
        return suffix

    normalized_content_type = 规范化内容类型(content_type)
    for ext, mapped_content_type in 扩展名到媒体类型映射.items():
        if mapped_content_type == normalized_content_type:
            return ext
    return ""


def 推断内容类型(content_type: str, filename: str) -> str:
    """优先使用上传声明的媒体类型，其次从扩展名推断。"""
    normalized_content_type = 规范化内容类型(content_type)
    if normalized_content_type:
        return normalized_content_type

    return 扩展名到媒体类型映射.get(
        推断扩展名(filename, normalized_content_type),
        "application/octet-stream",
    )


def 构建回退文件名(filename: str, content_type: str) -> str:
    """为空文件名生成兜底名称。"""
    stripped_filename = filename.strip()
    if stripped_filename:
        return stripped_filename

    ext = 推断扩展名(filename, content_type)
    normalized_content_type = 推断内容类型(content_type, filename)
    stem = 默认图片文件名 if normalized_content_type.startswith("image/") else 默认普通文件名
    return f"{stem}{ext}" if ext else stem


def 构建目标文件名(source_filename: str, target_ext: str) -> str:
    """基于原始名称生成目标格式文件名。"""
    fallback_filename = 构建回退文件名(source_filename, "")
    stem = Path(fallback_filename).stem.strip()
    if not stem or stem == ".":
        stem = 默认图片文件名
    return f"{stem}{target_ext}"


def 按内容类型规范化文件名(filename: str, content_type: str) -> str:
    """让展示文件名与真实内容类型保持一致。"""
    fallback_filename = 构建回退文件名(filename, content_type)
    normalized_content_type = 推断内容类型(content_type, fallback_filename)
    if normalized_content_type == "image/avif":
        return 构建目标文件名(fallback_filename, ".avif")
    return fallback_filename


def 是否为图片上传(filename: str, content_type: str) -> bool:
    """根据扩展名与媒体类型判断是否为图片。"""
    ext = 推断扩展名(filename, content_type)
    normalized_content_type = 推断内容类型(content_type, filename)
    return normalized_content_type.startswith("image/") or ext in 图片扩展名


def 是否为SVG上传(filename: str, content_type: str) -> bool:
    """判断是否为 SVG 矢量图。"""
    ext = 推断扩展名(filename, content_type)
    normalized_content_type = 推断内容类型(content_type, filename)
    return ext == ".svg" or normalized_content_type == "image/svg+xml"


def 是否为AVIF上传(filename: str, content_type: str) -> bool:
    """判断是否已经是 AVIF。"""
    ext = 推断扩展名(filename, content_type)
    normalized_content_type = 推断内容类型(content_type, filename)
    return ext == ".avif" or normalized_content_type == "image/avif"


def 是否为动图(image: Image.Image) -> bool:
    """判断图片是否包含多帧动画。"""
    return bool(getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1)


def 是否为GIF上传(filename: str, content_type: str) -> bool:
    """判断是否为 GIF 图片。"""
    ext = 推断扩展名(filename, content_type)
    normalized_content_type = 推断内容类型(content_type, filename)
    return ext == ".gif" or normalized_content_type == "image/gif"


def 规范化光栅图片(image: Image.Image) -> Image.Image:
    """统一栅格图的方向与色彩模式，便于编码为 AVIF。"""
    normalized_image = ImageOps.exif_transpose(image)
    if (
        normalized_image.mode in {"RGBA", "LA"}
        or (normalized_image.mode == "P" and "transparency" in normalized_image.info)
    ):
        return normalized_image.convert("RGBA")
    return normalized_image.convert("RGB")


def 转换图片为AVIF(content: bytes) -> bytes:
    """将静态位图转换为 AVIF。"""
    with Image.open(io.BytesIO(content)) as image:
        normalized_image = 规范化光栅图片(image)
        output = io.BytesIO()
        normalized_image.save(output, format="AVIF", quality=AVIF质量)
        return output.getvalue()


def 转换动图为AVIF(content: bytes) -> bytes:
    """将多帧位图转换为动图 AVIF。"""
    with Image.open(io.BytesIO(content)) as image:
        frames = [规范化光栅图片(frame.copy()) for frame in ImageSequence.Iterator(image)]
        if not frames:
            raise ValueError("缺少可转换的动画帧")

        durations = []
        for frame_index in range(len(frames)):
            try:
                image.seek(frame_index)
            except EOFError:
                break
            durations.append(int(image.info.get("duration", 0)))

        output = io.BytesIO()
        first_frame, *remaining_frames = frames
        loop = image.info.get("loop")
        if durations and loop is not None:
            first_frame.save(
                output,
                format="AVIF",
                quality=AVIF质量,
                save_all=True,
                append_images=remaining_frames,
                duration=durations,
                loop=loop,
            )
        elif durations:
            first_frame.save(
                output,
                format="AVIF",
                quality=AVIF质量,
                save_all=True,
                append_images=remaining_frames,
                duration=durations,
            )
        elif loop is not None:
            first_frame.save(
                output,
                format="AVIF",
                quality=AVIF质量,
                save_all=True,
                append_images=remaining_frames,
                loop=loop,
            )
        else:
            first_frame.save(
                output,
                format="AVIF",
                quality=AVIF质量,
                save_all=True,
                append_images=remaining_frames,
            )
        return output.getvalue()


def 准备上传载荷(
    filename: str,
    content_type: str,
    content: bytes,
    *,
    compress_static_images: bool,
) -> PreparedUpload:
    """将上传内容规范化为最终存储格式。"""
    resolved_content_type = 推断内容类型(content_type, filename)
    resolved_filename = 按内容类型规范化文件名(filename, resolved_content_type)

    if not 是否为图片上传(resolved_filename, resolved_content_type):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    if not compress_static_images:
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    if 是否为SVG上传(resolved_filename, resolved_content_type) or 是否为AVIF上传(
        resolved_filename,
        resolved_content_type,
    ):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    try:
        with Image.open(io.BytesIO(content)) as image:
            if 是否为动图(image):
                if 是否为GIF上传(resolved_filename, resolved_content_type):
                    converted_content = 转换动图为AVIF(content)
                    converted_filename = 按内容类型规范化文件名(
                        resolved_filename,
                        "image/avif",
                    )
                    return PreparedUpload(
                        original_name=converted_filename,
                        storage_name=converted_filename,
                        content=converted_content,
                        content_type="image/avif",
                    )
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

    converted_content = 转换图片为AVIF(content)
    converted_filename = 按内容类型规范化文件名(resolved_filename, "image/avif")
    return PreparedUpload(
        original_name=converted_filename,
        storage_name=converted_filename,
        content=converted_content,
        content_type="image/avif",
    )
