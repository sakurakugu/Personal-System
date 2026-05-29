"""公开文件读取路由。"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
import hashlib
import io
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from minio.error import S3Error
from PIL import Image, ImageOps, UnidentifiedImageError
import pillow_avif  # noqa: F401
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import Response, StreamingResponse

from app.shared.auth.deps import (
    获取当前用户可选,
)
from app.modules.articles.models import 文章图片, 文章状态
from app.modules.articles.permissions import 用户可否阅读文章
from app.modules.moments.models import 动态图片
from app.modules.moments.permissions import 用户可否阅读动态
from app.modules.files.models import File, FilePurpose
from app.modules.media.models import 文娱资源, 文娱条目
from app.modules.users.models import 用户
from app.shared.db.session import get_db
from app.shared.storage.client import 获取对象字节, 打开对象流
from app.shared.storage.file_url import 验证已签署文件请求

router = APIRouter(prefix="/files", tags=["public-files"])
缩略图最大尺寸 = 512
文件缓存秒数 = 300


def 用户可否管理已删除文章图片(user: 用户 | None, article_image: 文章图片) -> bool:
    """判断用户是否可读取已删除文章的图片。"""
    if user is None or article_image.article is None:
        return False
    if article_image.article.author_id == user.id:
        return True
    return user.role.value in ("admin", "super_admin")


def 用户可否管理已删除动态图片(user: 用户 | None, moment_image: 动态图片) -> bool:
    """判断用户是否可读取已删除动态的图片。"""
    if user is None or moment_image.moment is None:
        return False
    if moment_image.moment.user_id == user.id:
        return True
    return user.role.value in ("admin", "super_admin")


def 构建文件响应头(original_name: str, *, content_length: int | None) -> dict[str, str]:
    """构造文件响应头。"""
    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(original_name)}"}
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    return headers


def 规范化HTTP日期时间(value: datetime) -> datetime:
    """将时间统一转换为 HTTP 响应头可用的 UTC 秒级时间。"""
    return value.astimezone(timezone.utc).replace(microsecond=0)


def 构建资源ETag(
    storage_key: str,
    *,
    source_size: int,
    source_mime_type: str,
    source_created_at: datetime,
    variant_key: str,
) -> str:
    """根据稳定元数据构造资源实体标签。"""
    payload = "\n".join(
        [
            storage_key,
            str(source_size),
            source_mime_type,
            规范化HTTP日期时间(source_created_at).isoformat(),
            variant_key,
        ]
    )
    return f'"{hashlib.sha256(payload.encode("utf-8")).hexdigest()}"'


def 构建缩略图ETag(
    storage_key: str,
    *,
    source_size: int,
    source_mime_type: str,
    source_created_at: datetime,
    width: int,
    height: int,
) -> str:
    """根据稳定元数据构造缩略图实体标签。"""
    return 构建资源ETag(
        storage_key,
        source_size=source_size,
        source_mime_type=source_mime_type,
        source_created_at=source_created_at,
        variant_key=f"thumbnail:{width}x{height}",
    )


def 构建原文件ETag(
    storage_key: str,
    *,
    source_size: int,
    source_mime_type: str,
    source_created_at: datetime,
) -> str:
    """根据稳定元数据构造原图或原文件实体标签。"""
    return 构建资源ETag(
        storage_key,
        source_size=source_size,
        source_mime_type=source_mime_type,
        source_created_at=source_created_at,
        variant_key="original",
    )


def 构建资源缓存头(etag: str, last_modified: datetime) -> dict[str, str]:
    """构造资源缓存相关响应头。"""
    return {
        "Cache-Control": f"private, max-age={文件缓存秒数}",
        "ETag": etag,
        "Last-Modified": format_datetime(规范化HTTP日期时间(last_modified), usegmt=True),
    }


def 构建公开资源缓存头(etag: str, last_modified: datetime) -> dict[str, str]:
    """构造可公开读取资源的缓存响应头。"""
    headers = 构建资源缓存头(etag, last_modified)
    headers["Cache-Control"] = f"public, max-age={文件缓存秒数}"
    return headers


def 规范化ETag值(value: str) -> str:
    """将请求头中的 ETag 规范化为可比较的值。"""
    normalized = value.strip()
    if normalized.startswith("W/"):
        normalized = normalized[2:].strip()
    return normalized.strip('"')


def 资源是否未修改(
    *,
    etag: str,
    last_modified: datetime,
    if_none_match: str | None,
    if_modified_since: str | None,
) -> bool:
    """根据条件请求头判断资源是否可直接返回 304。"""
    normalized_etag = 规范化ETag值(etag)
    if if_none_match:
        candidates = [item.strip() for item in if_none_match.split(",") if item.strip()]
        if "*" in candidates:
            return True
        return any(规范化ETag值(candidate) == normalized_etag for candidate in candidates)

    if not if_modified_since:
        return False

    try:
        parsed_value = parsedate_to_datetime(if_modified_since)
    except (TypeError, ValueError, IndexError):
        return False

    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(tzinfo=timezone.utc)
    return parsed_value.astimezone(timezone.utc) >= 规范化HTTP日期时间(last_modified)


def 解析缩略图尺寸(width: int | None, height: int | None) -> tuple[int, int] | None:
    """解析缩略图目标尺寸。"""
    if width is None and height is None:
        return None

    resolved_width = width or height
    resolved_height = height or width
    if resolved_width is None or resolved_height is None:
        return None
    return resolved_width, resolved_height


def 是否应生成缩略图(content_type: str, size: tuple[int, int] | None) -> bool:
    """判断当前请求是否需要生成缩略图。"""
    return (
        size is not None and content_type.startswith("image/") and content_type != "image/svg+xml"
    )


def 构建图片缩略图(content: bytes, *, width: int, height: int) -> bytes:
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
async def 获取公开文件(
    storage_key: str,
    expires: Annotated[int | None, Query()] = None,
    signature: Annotated[str | None, Query()] = None,
    thumbnail_width: Annotated[int | None, Query(ge=24, le=缩略图最大尺寸)] = None,
    thumbnail_height: Annotated[int | None, Query(ge=24, le=缩略图最大尺寸)] = None,
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """按对象存储路径返回文件内容，并对文章图片执行权限校验。"""
    resolved_user = user
    允许公开缓存 = False
    has_valid_signature = 验证已签署文件请求(
        storage_key,
        expires_at=expires,
        signature=signature,
        query_params={
            "thumbnail_width": thumbnail_width,
            "thumbnail_height": thumbnail_height,
        },
    )
    original_name = ""
    content_type = ""
    source_size = 0
    source_created_at: datetime | None = None

    article_image_result = await db.execute(
        select(文章图片)
        .options(selectinload(文章图片.article))
        .where(文章图片.storage_key == storage_key)
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is not None:
        article = article_image.article
        if article.is_deleted:
            if not 用户可否管理已删除文章图片(resolved_user, article_image):
                raise HTTPException(status_code=404, detail="文件不存在")
        elif not has_valid_signature and not 用户可否阅读文章(article, resolved_user):
            if article.status == 文章状态.login_required:
                raise HTTPException(status_code=401, detail="该文章需要登录后查看")
            raise HTTPException(status_code=404, detail="文件不存在")
        original_name = article_image.original_name
        content_type = article_image.mime_type
        source_size = article_image.size
        source_created_at = article_image.created_at

    else:
        moment_image_result = await db.execute(
            select(动态图片)
            .options(selectinload(动态图片.moment))
            .where(动态图片.storage_key == storage_key)
        )
        moment_image = moment_image_result.scalar_one_or_none()
        if moment_image is not None:
            moment = moment_image.moment
            if moment.is_deleted:
                if not 用户可否管理已删除动态图片(resolved_user, moment_image):
                    raise HTTPException(status_code=404, detail="文件不存在")
            elif not has_valid_signature and not 用户可否阅读动态(moment, resolved_user):
                if moment.is_published:
                    raise HTTPException(status_code=401, detail="该动态需要登录后查看")
                raise HTTPException(status_code=404, detail="文件不存在")
            original_name = moment_image.original_name
            content_type = moment_image.mime_type
            source_size = moment_image.size
            source_created_at = moment_image.created_at

        else:
            media_asset_result = await db.execute(
                select(文娱资源)
                .options(selectinload(文娱资源.media_item))
                .where(文娱资源.storage_key == storage_key)
            )
            media_asset = media_asset_result.scalar_one_or_none()
            if media_asset is not None:
                media_item: 文娱条目 | None = media_asset.media_item
                允许公开读取文娱资源 = bool(
                    media_item
                    and media_item.is_visible
                    and not media_item.is_deleted
                    and media_asset.asset_type == "cover"
                )
                if not has_valid_signature:
                    if 允许公开读取文娱资源:
                        允许公开缓存 = True
                    else:
                        if resolved_user is None:
                            raise HTTPException(status_code=401, detail="未登录")
                        if media_asset.user_id != resolved_user.id:
                            raise HTTPException(status_code=404, detail="文件不存在")
                elif 允许公开读取文娱资源:
                    允许公开缓存 = True
                original_name = media_asset.original_name or "media-asset"
                content_type = media_asset.mime_type or "application/octet-stream"
                source_size = media_asset.size or 0
                source_created_at = media_asset.created_at
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
                if not has_valid_signature:
                    if resolved_user is None:
                        raise HTTPException(status_code=401, detail="未登录")
                    if file_record.user_id != resolved_user.id:
                        raise HTTPException(status_code=404, detail="文件不存在")
                original_name = file_record.original_name
                content_type = file_record.mime_type
                source_size = file_record.size
                source_created_at = file_record.created_at

    thumbnail_size = 解析缩略图尺寸(thumbnail_width, thumbnail_height)
    if 是否应生成缩略图(content_type, thumbnail_size):
        assert thumbnail_size is not None
        assert source_created_at is not None
        resolved_thumbnail_width, resolved_thumbnail_height = thumbnail_size
        etag = 构建缩略图ETag(
            storage_key,
            source_size=source_size,
            source_mime_type=content_type,
            source_created_at=source_created_at,
            width=resolved_thumbnail_width,
            height=resolved_thumbnail_height,
        )
        cache_headers = (
            构建公开资源缓存头(etag, source_created_at)
            if 允许公开缓存
            else 构建资源缓存头(etag, source_created_at)
        )
        if 资源是否未修改(
            etag=etag,
            last_modified=source_created_at,
            if_none_match=if_none_match,
            if_modified_since=if_modified_since,
        ):
            return Response(status_code=304, headers=cache_headers)
        try:
            content, _ = 获取对象字节(storage_key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise HTTPException(status_code=404, detail="文件不存在") from exc
            raise HTTPException(status_code=502, detail="文件读取失败") from exc

        try:
            thumbnail_content = 构建图片缩略图(
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
                    **构建文件响应头(original_name, content_length=len(thumbnail_content)),
                    **cache_headers,
                },
            )

    assert source_created_at is not None
    original_etag = 构建原文件ETag(
        storage_key,
        source_size=source_size,
        source_mime_type=content_type,
        source_created_at=source_created_at,
    )
    original_cache_headers = (
        构建公开资源缓存头(original_etag, source_created_at)
        if 允许公开缓存
        else 构建资源缓存头(original_etag, source_created_at)
    )
    if 资源是否未修改(
        etag=original_etag,
        last_modified=source_created_at,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
    ):
        return Response(status_code=304, headers=original_cache_headers)

    try:
        object_stream = 打开对象流(storage_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="文件不存在") from exc
        raise HTTPException(status_code=502, detail="文件读取失败") from exc

    return StreamingResponse(
        object_stream.chunks,
        media_type=object_stream.content_type,
        headers={
            **构建文件响应头(original_name, content_length=object_stream.content_length),
            **original_cache_headers,
        },
    )
