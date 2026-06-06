"""文娱相关 MCP 工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.media.models import 文娱条目
from app.modules.media.schemas import 文娱主分类, 文娱条目信息, 文娱条目创建, 文娱条目更新, 文娱筛选项, 文娱状态
from app.modules.media.service import (
    get_media_or_404,
    创建文娱,
    列出文娱,
    列出文娱创作者建议,
    列出文娱标签,
    列出文娱类型,
    删除文娱,
    恢复文娱,
    更新文娱,
    获取已删文娱或404,
    构建文娱读取,
)


class 文娱列表参数(BaseModel):
    """当前用户文娱列表查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    media_type: 文娱主分类 | None = Field(default=None, description="文娱主分类")
    status: 文娱状态 | None = Field(default=None, description="文娱状态")
    rating: int | None = Field(default=None, ge=1, le=15, description="评分")
    keyword: str | None = Field(default=None, max_length=100, description="关键词")
    genre: str | None = Field(default=None, max_length=100, description="分类标签")
    tag: str | None = Field(default=None, max_length=100, description="标签")
    personal_tag: str | None = Field(default=None, max_length=100, description="个人标签")
    is_deleted: bool = Field(default=False, description="是否查询回收站")


class 文娱聚合筛选参数(BaseModel):
    """文娱聚合筛选参数。"""

    media_type: 文娱主分类 | None = Field(default=None, description="按文娱主分类筛选标签统计")
    creator_keyword: str | None = Field(default=None, max_length=100, description="创作者关键词")
    creator_limit: int = Field(default=20, ge=1, le=50, description="创作者返回数量")


class 文娱ID参数(BaseModel):
    """单条文娱 ID 参数。"""

    media_id: str = Field(description="文娱条目 ID")


class 文娱元信息更新参数(文娱ID参数):
    """文娱低风险元信息更新参数。"""

    expected_updated_at: str = Field(description="调用方读取到的 updated_at")
    title: str | None = Field(default=None, min_length=1, max_length=300)
    original_title: str | None = Field(default=None, max_length=300)
    media_type: 文娱主分类 | None = None
    status: 文娱状态 | None = None
    rating: int | None = Field(default=None, ge=1, le=15)
    creator: str | None = Field(default=None, max_length=200)
    summary: str | None = None
    description: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    personal_tags: list[str] | None = None
    release_date: str | None = Field(default=None, description="发行日期，格式 YYYY-MM-DD")
    is_visible: bool | None = Field(default=None, description="公开可见性")


def _获取MCP会话(context: MCP调用上下文):
    """获取当前 MCP 运行时数据库会话。"""
    if context.db is None:
        raise RuntimeError("MCP 工具缺少数据库会话")
    return context.db


def _解析时间戳(value: str) -> datetime:
    """解析 ISO 时间戳。"""
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expected_updated_at 格式无效") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _转UTC(value: datetime) -> datetime:
    """将数据库时间戳转为 UTC。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def 校验文娱更新时间(actual: datetime, expected: str) -> None:
    """校验调用方读取的文娱更新时间仍然有效。"""
    if _转UTC(actual) != _解析时间戳(expected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "文娱条目已被更新，请重新读取后再修改",
                "current_updated_at": actual.isoformat(),
            },
        )


def _文娱读取(item: 文娱条目信息) -> dict[str, Any]:
    """将文娱响应模型转为稳定 JSON。"""
    return item.model_dump(mode="json")


def _筛选项列表(items: list[文娱筛选项]) -> list[dict[str, Any]]:
    """将筛选项列表转为稳定 JSON。"""
    return [item.model_dump(mode="json") for item in items]


def _文娱详情(item: 文娱条目) -> dict[str, Any]:
    """将文娱 ORM 对象转为稳定 JSON。"""
    return _文娱读取(构建文娱读取(item))


def _文娱元信息快照(item: 文娱条目) -> dict[str, Any]:
    """构建文娱元信息撤销快照，不包含资源和外部来源。"""
    return {
        "id": str(item.id),
        "title": item.title,
        "original_title": item.original_title,
        "media_type": item.media_type,
        "status": item.status,
        "rating": item.rating,
        "creator": item.creator,
        "summary": item.summary,
        "description": item.description,
        "genres": item.genres or [],
        "tags": item.tags or [],
        "personal_tags": item.personal_tags or [],
        "release_date": item.release_date.isoformat() if item.release_date else None,
        "is_visible": item.is_visible,
        "is_deleted": item.is_deleted,
        "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _构建元信息更新载荷(args: dict[str, Any]) -> 文娱条目更新:
    """从 MCP 参数构建文娱元信息更新载荷。"""
    allowed = {
        "title",
        "original_title",
        "media_type",
        "status",
        "rating",
        "creator",
        "summary",
        "description",
        "genres",
        "tags",
        "personal_tags",
        "release_date",
        "is_visible",
    }
    payload = {key: value for key, value in args.items() if key in allowed}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少提供一个可更新的元信息字段")
    return 文娱条目更新.model_validate(payload)


async def media_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查询当前用户文娱条目列表。"""
    body = 文娱列表参数.model_validate(args)
    response = await 列出文娱(
        _获取MCP会话(context),
        context.user,
        page=body.page,
        page_size=body.page_size,
        media_type=body.media_type,
        status=body.status,
        rating=body.rating,
        keyword=body.keyword,
        genre=body.genre,
        tag=body.tag,
        personal_tag=body.personal_tag,
        is_deleted=body.is_deleted,
    )
    return {
        "items": [_文娱读取(item) for item in response.items],
        "total": response.total,
        "page": response.page,
        "page_size": response.page_size,
        "pages": response.pages,
        "all_data_updated_at": response.all_data_updated_at.isoformat() if response.all_data_updated_at else None,
    }


async def media_facets(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """聚合读取当前用户文娱库的筛选维度统计。"""
    body = 文娱聚合筛选参数.model_validate(args)
    db = _获取MCP会话(context)
    creators = await 列出文娱创作者建议(
        db,
        context.user,
        keyword=body.creator_keyword,
        limit=body.creator_limit,
    )
    return {
        "summary": "已读取文娱筛选维度统计",
        "media_type_filter": body.media_type,
        "types": _筛选项列表(await 列出文娱类型(db, context.user)),
        "genres": _筛选项列表(
            await 列出文娱标签(db, context.user, field_name="genres", media_type=body.media_type)
        ),
        "tags": _筛选项列表(
            await 列出文娱标签(db, context.user, field_name="tags", media_type=body.media_type)
        ),
        "personal_tags": _筛选项列表(
            await 列出文娱标签(db, context.user, field_name="personal_tags", media_type=body.media_type)
        ),
        "creators": [item.model_dump(mode="json") for item in creators],
    }


async def media_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取当前用户的一条文娱详情。"""
    body = 文娱ID参数.model_validate(args)
    item = await get_media_or_404(_获取MCP会话(context), context.user, body.media_id)
    return _文娱详情(item)


async def media_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """手动创建当前用户文娱条目。"""
    body = 文娱条目创建.model_validate(args)
    if body.primary_cover_asset_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MCP 创建文娱暂不支持绑定封面资源")
    item = await 创建文娱(_获取MCP会话(context), context.user, body)
    return {
        "summary": f"已创建文娱条目：{item.title}",
        "target": {"type": "media", "id": str(item.id)},
        "undoable": True,
        "undo_tool_name": "media.delete",
        "after": item.model_dump(mode="json"),
        "data": _文娱读取(item),
    }


async def media_update_metadata(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """更新当前用户文娱条目的低风险元信息。"""
    body = 文娱元信息更新参数.model_validate(args)
    db = _获取MCP会话(context)
    before_item = await get_media_or_404(db, context.user, body.media_id)
    校验文娱更新时间(before_item.updated_at, body.expected_updated_at)
    before = _文娱元信息快照(before_item)
    updated = await 更新文娱(db, context.user, body.media_id, _构建元信息更新载荷(args))
    after_item = await get_media_or_404(db, context.user, body.media_id)
    after = _文娱元信息快照(after_item)
    return {
        "summary": f"已更新文娱元信息：{updated.title}",
        "target": {"type": "media", "id": str(updated.id)},
        "undoable": True,
        "undo_tool_name": "media.update_metadata",
        "before": before,
        "after": after,
        "data": _文娱读取(updated),
    }


async def media_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """将当前用户文娱条目移入回收站。"""
    body = 文娱ID参数.model_validate(args)
    db = _获取MCP会话(context)
    item = await get_media_or_404(db, context.user, body.media_id)
    before = _文娱元信息快照(item)
    title = item.title
    await 删除文娱(db, context.user, body.media_id, permanent=False)
    deleted = await 获取已删文娱或404(db, context.user, body.media_id)
    return {
        "summary": f"已移入回收站：{title}",
        "target": {"type": "media", "id": str(deleted.id)},
        "undoable": True,
        "undo_tool_name": "media.restore",
        "before": before,
        "after": _文娱元信息快照(deleted),
    }


async def media_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复当前用户文娱条目。"""
    body = 文娱ID参数.model_validate(args)
    db = _获取MCP会话(context)
    before_item = await 获取已删文娱或404(db, context.user, body.media_id)
    before = _文娱元信息快照(before_item)
    restored = await 恢复文娱(db, context.user, body.media_id)
    after_item = await get_media_or_404(db, context.user, body.media_id)
    return {
        "summary": f"已恢复文娱条目：{restored.title}",
        "target": {"type": "media", "id": str(restored.id)},
        "undoable": True,
        "undo_tool_name": "media.delete",
        "before": before,
        "after": _文娱元信息快照(after_item),
        "data": _文娱读取(restored),
    }


注册工具(
    MCP工具定义(
        name="media.list",
        description="查询当前用户文娱条目列表，支持分类、状态、评分、标签和关键词筛选。",
        input_schema=文娱列表参数.model_json_schema(),
        permission="readonly",
        handler=media_list,
    )
)
注册工具(
    MCP工具定义(
        name="media.facets",
        description="聚合读取当前用户文娱库的类型、子分类、标签、个人标签和创作者统计。",
        input_schema=文娱聚合筛选参数.model_json_schema(),
        permission="readonly",
        handler=media_facets,
    )
)
注册工具(
    MCP工具定义(
        name="media.get",
        description="读取当前用户的一条文娱条目详情。",
        input_schema=文娱ID参数.model_json_schema(),
        permission="readonly",
        handler=media_get,
    )
)
注册工具(
    MCP工具定义(
        name="media.create",
        description="手动创建当前用户文娱条目，不绑定封面资源；可通过撤销软删除新建条目。",
        input_schema=文娱条目创建.model_json_schema(),
        permission="full",
        handler=media_create,
    )
)
注册工具(
    MCP工具定义(
        name="media.update_metadata",
        description="更新当前用户文娱条目的标题、状态、评分、简介和标签等低风险元信息，必须提供 expected_updated_at。",
        input_schema=文娱元信息更新参数.model_json_schema(),
        permission="full",
        handler=media_update_metadata,
    )
)
注册工具(
    MCP工具定义(
        name="media.delete",
        description="将当前用户的一条文娱条目移入回收站，只执行软删除，不执行永久删除。",
        input_schema=文娱ID参数.model_json_schema(),
        permission="full",
        handler=media_delete,
    )
)
注册工具(
    MCP工具定义(
        name="media.restore",
        description="从回收站恢复当前用户的一条文娱条目。",
        input_schema=文娱ID参数.model_json_schema(),
        permission="full",
        handler=media_restore,
    )
)
