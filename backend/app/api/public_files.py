"""公开文件读取路由。"""

from __future__ import annotations

import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from minio.error import S3Error
from PIL import Image, ImageOps, UnidentifiedImageError
import pillow_avif  # type: ignore[import-untyped]  # noqa: F401
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import Response, StreamingResponse

from app.api.deps import (
    get_current_user_optional,
    get_user_from_access_token_optional,
)
from app.core.database import get_db
from app.models.article import ArticleImage, ArticleStatus
from app.models.file import File, FilePurpose
from app.models.user import User
from app.services.article_service import can_user_read_article
from app.services.storage_service import fetch_object_bytes, open_object_stream

router = APIRouter(prefix="/files", tags=["public-files"])
缩略图最大尺寸 = 512


def build_file_response_headers(original_name: str, *, content_length: int | None) -> dict[str, str]:
    """构造文件响应头。"""
    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(original_name)}"}
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    return headers


def resolve_thumbnail_size(width: int | None, height: int | None) -> tuple[int, int] | None:
    """解析缩略图目标尺寸。"""
    if width is None and height is None:
        return None

    resolved_width = width or height
    resolved_height = height or width
    if resolved_width is None or resolved_height is None:
        return None
    return resolved_width, resolved_height


def should_generate_thumbnail(content_type: str, size: tuple[int, int] | None) -> bool:
    """判断当前请求是否需要生成缩略图。"""
    return size is not None and content_type.startswith("image/") and content_type != "image/svg+xml"


def build_image_thumbnail(content: bytes, *, width: int, height: int) -> bytes:
    """将图片内容裁剪为缩略图。"""
    with Image.open(io.BytesIO(content)) as image:
        normalized_image = ImageOps.exif_transpose(image)
        if getattr(normalized_image, "is_animated", False):
            normalized_image.seek(0)

        if normalized_image.mode in {"RGBA", "LA"}:
            prepared_image = normalized_image.convert("RGBA")
        elif normalized_image.mode == "P" and "transparency" in normalized_image.info:
            prepared_image = normalized_image.convert("RGBA")
        else:
            prepared_image = normalized_image.convert("RGB")

        output = io.BytesIO()
        thumbnail = ImageOps.fit(prepared_image, (width, height), method=Image.Resampling.LANCZOS)
        thumbnail.save(output, format="PNG", optimize=True)
        return output.getvalue()


@router.get("/{storage_key:path}")
async def get_public_file(
    storage_key: str,
    access_token: str | None = Query(default=None),
    thumbnail_width: int | None = Query(default=None, ge=24, le=缩略图最大尺寸),
    thumbnail_height: int | None = Query(default=None, ge=24, le=缩略图最大尺寸),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """按对象存储路径返回文件内容，并对文章图片执行权限校验。"""
    resolved_user = await get_user_from_access_token_optional(access_token, db) or user
    original_name = ""
    content_type = ""

    article_image_result = await db.execute(
        select(ArticleImage)
        .options(selectinload(ArticleImage.article))
        .where(ArticleImage.storage_key == storage_key)
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is not None:
        article = article_image.article
        if not can_user_read_article(article, resolved_user):
            if article.status == ArticleStatus.login_required:
                raise HTTPException(status_code=401, detail="该文章需要登录后查看")
            raise HTTPException(status_code=404, detail="文件不存在")
        original_name = article_image.original_name
        content_type = article_image.mime_type

    else:
        file_result = await db.execute(
            select(File).where(
                File.storage_key == storage_key,
                File.purpose == FilePurpose.file,
            )
        )
        file_record = file_result.scalar_one_or_none()
        if file_record is None:
            raise HTTPException(status_code=404, detail="文件不存在")
        if resolved_user is None:
            raise HTTPException(status_code=401, detail="未登录")
        if file_record.user_id != resolved_user.id:
            raise HTTPException(status_code=404, detail="文件不存在")
        original_name = file_record.original_name
        content_type = file_record.mime_type

    thumbnail_size = resolve_thumbnail_size(thumbnail_width, thumbnail_height)
    if should_generate_thumbnail(content_type, thumbnail_size):
        assert thumbnail_size is not None
        resolved_thumbnail_width, resolved_thumbnail_height = thumbnail_size
        try:
            content, _ = fetch_object_bytes(storage_key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise HTTPException(status_code=404, detail="文件不存在") from exc
            raise HTTPException(status_code=502, detail="文件读取失败") from exc

        try:
            thumbnail_content = build_image_thumbnail(
                content,
                width=resolved_thumbnail_width,
                height=resolved_thumbnail_height,
            )
        except (UnidentifiedImageError, OSError, ValueError):
            thumbnail_content = b""

        if thumbnail_content:
            return Response(
                content=thumbnail_content,
                media_type="image/png",
                headers={
                    **build_file_response_headers(original_name, content_length=len(thumbnail_content)),
                    "Cache-Control": "private, max-age=300",
                },
            )

    try:
        object_stream = open_object_stream(storage_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="文件不存在") from exc
        raise HTTPException(status_code=502, detail="文件读取失败") from exc

    return StreamingResponse(
        object_stream.chunks,
        media_type=object_stream.content_type,
        headers=build_file_response_headers(original_name, content_length=object_stream.content_length),
    )
