"""动态响应序列化。"""

from __future__ import annotations

from sqlalchemy import inspect

from app.modules.moments.models import Moment, MomentImage
from app.modules.moments.schemas import MomentDraftRead, MomentImageRead, MomentPublicRead, MomentRead
from app.shared.storage.client import 构建公开URL
from app.shared.storage.file_url import 构建签名文件URL


def 构建动态图片读取(record: MomentImage) -> MomentImageRead:
    """构造动态图片响应。"""
    thumbnail_url = None
    if record.mime_type.startswith("image/") and record.mime_type != "image/svg+xml":
        thumbnail_url = 构建签名文件URL(
            record.storage_key,
            query_params={
                "thumbnail_width": 144,
                "thumbnail_height": 144,
            },
        )

    return MomentImageRead(
        id=record.id,
        original_name=record.original_name,
        url=构建公开URL(record.storage_key),
        preview_url=构建签名文件URL(record.storage_key),
        thumbnail_url=thumbnail_url,
        size=record.size,
        mime_type=record.mime_type,
        sort_order=record.sort_order,
        created_at=record.created_at,
    )


def _构建动态图片(moment: Moment) -> list[MomentImageRead]:
    if "images" in inspect(moment).unloaded:
        return []

    return [
        构建动态图片读取(image)
        for image in sorted(moment.images, key=lambda item: (item.sort_order, item.created_at))
    ]


def 构建动态读取响应(moment: Moment, *, liked: bool = False) -> MomentRead:
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
            "images": _构建动态图片(moment),
            "is_deleted": moment.is_deleted,
            "deleted_at": moment.deleted_at,
            "published_at": moment.published_at,
            "created_at": moment.created_at,
            "last_edited_at": moment.last_edited_at,
            "updated_at": moment.updated_at,
        }
    )


def 构建动态公开读取响应(moment: Moment, *, liked: bool = False) -> MomentPublicRead:
    """构造公开动态响应。"""
    return MomentPublicRead.model_validate(
        {
            "id": moment.id,
            "title": moment.title,
            "content": moment.content,
            "view_count": moment.view_count,
            "like_count": moment.like_count,
            "liked": liked,
            "images": _构建动态图片(moment),
            "published_at": moment.published_at,
            "last_edited_at": moment.last_edited_at,
            "user": moment.user,
        }
    )


def 构建动态草稿读取响应(moment: Moment) -> MomentDraftRead:
    """构造动态草稿响应。"""
    return MomentDraftRead.model_validate(
        {
            "id": moment.id,
            "title": moment.title,
            "content": moment.content,
            "images": _构建动态图片(moment),
            "is_deleted": moment.is_deleted,
            "deleted_at": moment.deleted_at,
            "last_edited_at": moment.last_edited_at,
            "updated_at": moment.updated_at,
        }
    )
