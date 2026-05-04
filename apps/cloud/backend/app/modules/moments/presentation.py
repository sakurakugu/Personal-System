"""动态响应序列化。"""

from __future__ import annotations

from sqlalchemy import inspect

from app.modules.moments.models import Moment, MomentImage
from app.modules.moments.schemas import MomentDraftRead, MomentImageRead, MomentPublicRead, MomentRead
from app.shared.storage.client import build_public_url
from app.shared.storage.file_url import build_signed_file_url


def build_moment_image_read(record: MomentImage) -> MomentImageRead:
    """构造动态图片响应。"""
    thumbnail_url = None
    if record.mime_type.startswith("image/") and record.mime_type != "image/svg+xml":
        thumbnail_url = build_signed_file_url(
            record.storage_key,
            query_params={
                "thumbnail_width": 144,
                "thumbnail_height": 144,
            },
        )

    return MomentImageRead(
        id=record.id,
        original_name=record.original_name,
        url=build_public_url(record.storage_key),
        preview_url=build_signed_file_url(record.storage_key),
        thumbnail_url=thumbnail_url,
        size=record.size,
        mime_type=record.mime_type,
        sort_order=record.sort_order,
        created_at=record.created_at,
    )


def _build_moment_images(moment: Moment) -> list[MomentImageRead]:
    if "images" in inspect(moment).unloaded:
        return []

    return [
        build_moment_image_read(image)
        for image in sorted(moment.images, key=lambda item: (item.sort_order, item.created_at))
    ]


def build_moment_read_response(moment: Moment, *, liked: bool = False) -> MomentRead:
    """构造动态详情响应。"""
    return MomentRead.model_validate(
        {
            "id": moment.id,
            "title": moment.title,
            "content": moment.content,
            "is_published": moment.is_published,
            "view_count": moment.view_count,
            "like_count": moment.like_count,
            "liked": liked,
            "user_id": moment.user_id,
            "images": _build_moment_images(moment),
            "published_at": moment.published_at,
            "created_at": moment.created_at,
            "updated_at": moment.updated_at,
        }
    )


def build_moment_public_read_response(moment: Moment, *, liked: bool = False) -> MomentPublicRead:
    """构造公开动态响应。"""
    return MomentPublicRead.model_validate(
        {
            "id": moment.id,
            "title": moment.title,
            "content": moment.content,
            "view_count": moment.view_count,
            "like_count": moment.like_count,
            "liked": liked,
            "images": _build_moment_images(moment),
            "published_at": moment.published_at,
            "user": moment.user,
        }
    )


def build_moment_draft_read_response(moment: Moment) -> MomentDraftRead:
    """构造动态草稿响应。"""
    return MomentDraftRead.model_validate(
        {
            "id": moment.id,
            "title": moment.title,
            "content": moment.content,
            "images": _build_moment_images(moment),
            "updated_at": moment.updated_at,
        }
    )
