"""资料库相关 MCP 工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.articles.models import 标签
from app.modules.articles.schemas import 标签创建, 文章创建
from app.modules.articles.service import 创建文章
from app.modules.articles.taxonomy import 创建标签 as 创建文章标签
from app.modules.files.presentation import 构建文件读取
from app.modules.materials.models import 资料
from app.modules.materials.schemas import 资料创建, 资料信息, 资料更新, 资料资产输入
from app.modules.materials.service import (
    get_material_or_404,
    创建资料,
    列出资料,
    删除资料,
    恢复资料,
    更新资料,
    获取已删资料或404,
    列出资料标签,
)
from app.modules.todos.schemas import TodoCreate, TodoRead
from app.modules.todos.service import create_todo

资料状态参数 = Literal["active", "archived"]
资料类型参数 = Literal["link", "text", "image", "file"]


class 资料列表参数(BaseModel):
    """当前用户资料库列表查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: 资料状态参数 | None = Field(default=None, description="资料状态")
    type: 资料类型参数 | None = Field(default=None, description="资料类型")
    tag: str | None = Field(default=None, max_length=50, description="标签")
    keyword: str | None = Field(default=None, max_length=100, description="关键词")
    is_deleted: bool = Field(default=False, description="是否查询回收站")


class 资料ID参数(BaseModel):
    """单条资料 ID 参数。"""

    material_id: str = Field(description="资料 ID")
    is_deleted: bool = Field(default=False, description="是否读取回收站资料")


class 资料标签列表参数(BaseModel):
    """资料库标签列表参数。"""

    is_deleted: bool = Field(default=False, description="是否统计回收站标签")


class 资料更新参数(BaseModel):
    """资料库更新参数。"""

    material_id: str = Field(description="资料 ID")
    expected_updated_at: str = Field(description="调用方读取到的 updated_at")
    type: 资料类型参数 | None = Field(default=None, description="资料类型")
    title: str | None = Field(default=None, max_length=300, description="标题")
    content_text: str | None = Field(default=None, description="正文或链接")
    note: str | None = Field(default=None, description="备注")
    status: 资料状态参数 | None = Field(default=None, description="资料状态")
    tags: list[str] | None = Field(default=None, description="标签")
    assets: list[资料资产输入] | None = Field(default=None, description="附件关系")


class 资料转资料库参数(BaseModel):
    """从现有资料复制生成新资料的参数。"""

    material_id: str = Field(description="来源资料 ID")
    type: 资料类型参数 | None = Field(default=None, description="目标资料类型，默认沿用来源")
    title: str | None = Field(default=None, max_length=300, description="目标标题，默认沿用来源")
    content_text: str | None = Field(default=None, description="目标正文，默认沿用来源")
    note: str | None = Field(default=None, description="目标备注，默认沿用来源")
    status: 资料状态参数 = Field(default="active", description="目标资料状态")
    tags: list[str] | None = Field(default=None, description="目标标签，默认沿用来源标签")
    include_assets: bool = Field(default=True, description="是否复制附件关系")


class 资料转文章参数(BaseModel):
    """从资料创建文章的参数。"""

    material_id: str = Field(description="来源资料 ID")
    title: str | None = Field(default=None, max_length=300, description="文章标题，默认使用资料标题")
    content: str | None = Field(default=None, description="文章正文，默认由资料正文、备注和附件链接组合")
    excerpt: str | None = Field(default=None, max_length=500, description="文章摘要，默认从资料备注或正文截取")
    cover_url: str | None = Field(default=None, max_length=500, description="文章封面")
    status: Literal["private", "login_required", "public"] = Field(default="private", description="文章状态")
    category_id: UUID | None = Field(default=None, description="文章分类 ID")
    tag_ids: list[UUID] | None = Field(default=None, description="文章标签 ID，提供后优先使用")
    tag_names: list[str] | None = Field(default=None, description="文章标签名称，默认沿用资料标签并自动创建缺失标签")
    include_assets: bool = Field(default=True, description="默认正文是否包含附件链接")


class 资料转待办参数(BaseModel):
    """从资料创建待办的参数。"""

    material_id: str = Field(description="来源资料 ID")
    title: str | None = Field(default=None, max_length=300, description="待办标题，默认使用资料标题")
    description: str | None = Field(default=None, description="待办描述，默认由资料正文、备注和附件链接组合")
    importance: int = Field(default=33, ge=0, le=100, description="重要程度")
    urgency: int = Field(default=33, ge=0, le=100, description="紧急程度")
    is_pinned: bool = Field(default=False, description="是否置顶")
    tags: list[str] | None = Field(default=None, description="待办标签，默认沿用资料标签")


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


def 校验资料更新时间(actual: datetime, expected: str) -> None:
    """校验调用方读取的资料库更新时间仍然有效。"""
    if _转UTC(actual) != _解析时间戳(expected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "资料库条目已被更新，请重新读取后再修改",
                "current_updated_at": actual.isoformat(),
            },
        )


def _资料读取(item: 资料信息, *, include_asset_detail: bool) -> dict[str, Any]:
    """将资料库响应模型转为稳定 JSON。"""
    data = item.model_dump(mode="json")
    if not include_asset_detail:
        data["assets"] = [
            {"id": asset["id"], "file_id": asset["file_id"], "sort_order": asset["sort_order"]}
            for asset in data.get("assets", [])
        ]
    return data


def _资料附件快照(material: 资料) -> list[dict[str, Any]]:
    """构建资料库附件关系快照。"""
    return [
        {
            "id": str(asset.id),
            "file_id": str(asset.file_id),
            "sort_order": asset.sort_order,
        }
        for asset in sorted(material.assets, key=lambda item: (item.sort_order, item.created_at))
    ]


def _资料附件输入(material: 资料) -> list[资料资产输入]:
    """构建资料库附件写入参数。"""
    return [
        资料资产输入(file_id=asset.file_id, sort_order=index)
        for index, asset in enumerate(sorted(material.assets, key=lambda item: (item.sort_order, item.created_at)))
    ]


def _资料快照(material: 资料) -> dict[str, Any]:
    """构建资料库撤销快照。"""
    return {
        "id": str(material.id),
        "type": material.type.value,
        "title": material.title,
        "content_text": material.content_text,
        "note": material.note,
        "status": material.status.value,
        "tags": material.tags or [],
        "assets": _资料附件快照(material),
        "archived_at": material.archived_at.isoformat() if material.archived_at else None,
        "is_deleted": material.is_deleted,
        "deleted_at": material.deleted_at.isoformat() if material.deleted_at else None,
        "created_at": material.created_at.isoformat(),
        "updated_at": material.updated_at.isoformat(),
    }


def _规范化转换标签(tag_names: list[str] | None) -> list[str]:
    """规范化转换目标标签。"""
    if not tag_names:
        return []
    return list(dict.fromkeys(tag.strip() for tag in tag_names if tag.strip()))


def _资料默认标题(material: 资料) -> str:
    """为转换目标生成稳定默认标题。"""
    for value in (material.title, material.content_text, material.note):
        normalized = (value or "").strip()
        if normalized:
            return normalized.splitlines()[0][:300]
    return f"未命名资料 {material.id}"


def _资料默认摘要(material: 资料) -> str | None:
    """从资料生成默认文章摘要。"""
    for value in (material.note, material.content_text, material.title):
        normalized = (value or "").strip()
        if normalized:
            return normalized[:500]
    return None


def _资料附件Markdown(material: 资料) -> str:
    """把资料附件转换为 Markdown 链接列表。"""
    lines: list[str] = []
    for asset in sorted(material.assets, key=lambda item: (item.sort_order, item.created_at)):
        file_data = 构建文件读取(asset.file)
        lines.append(f"- [{file_data.original_name}]({file_data.url})")
    return "\n".join(lines)


def _资料默认正文(material: 资料, *, include_assets: bool) -> str:
    """从资料生成适合文章或待办描述的正文。"""
    parts: list[str] = []
    if material.content_text:
        parts.append(material.content_text.strip())
    if material.note:
        parts.append(f"## 备注\n\n{material.note.strip()}")
    if include_assets and material.assets:
        parts.append(f"## 附件\n\n{_资料附件Markdown(material)}")
    if parts:
        return "\n\n".join(parts)
    return _资料默认标题(material)


async def _获取或创建文章标签ID(db, tag_names: list[str]) -> list[UUID]:
    """按名称复用或创建文章标签，并返回 ID。"""
    normalized_names = _规范化转换标签(tag_names)
    if not normalized_names:
        return []

    result = await db.execute(select(标签).where(标签.name.in_(normalized_names)))
    existing_tags = {tag.name: tag for tag in result.scalars().all()}
    tag_ids: list[UUID] = []
    for name in normalized_names:
        tag = existing_tags.get(name)
        if tag is None:
            tag = await 创建文章标签(db, 标签创建(name=name))
            existing_tags[name] = tag
        tag_ids.append(tag.id)
    return tag_ids


def _构建资料更新载荷(args: dict[str, Any]) -> 资料更新:
    """从 MCP 参数构建资料库更新载荷。"""
    allowed = {"type", "title", "content_text", "note", "status", "tags", "assets"}
    payload = {key: value for key, value in args.items() if key in allowed}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少提供一个可更新的资料库字段")
    return 资料更新.model_validate(payload)


async def materials_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查询当前用户资料库列表。"""
    body = 资料列表参数.model_validate(args)
    response = await 列出资料(
        _获取MCP会话(context),
        context.user,
        page=body.page,
        page_size=body.page_size,
        status=body.status,
        material_type=body.type,
        tag=body.tag,
        keyword=body.keyword,
        is_deleted=body.is_deleted,
    )
    return {
        "items": [_资料读取(item, include_asset_detail=False) for item in response.items],
        "total": response.total,
        "page": response.page,
        "page_size": response.page_size,
        "pages": response.pages,
    }


async def materials_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取当前用户的一条资料详情。"""
    body = 资料ID参数.model_validate(args)
    db = _获取MCP会话(context)
    material = (
        await 获取已删资料或404(db, context.user, body.material_id)
        if body.is_deleted
        else await get_material_or_404(db, context.user, body.material_id)
    )
    return _资料快照(material)


async def materials_tags_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查看当前用户资料库标签统计。"""
    body = 资料标签列表参数.model_validate(args)
    tags = await 列出资料标签(_获取MCP会话(context), context.user, is_deleted=body.is_deleted)
    return {"items": [item.model_dump(mode="json") for item in tags], "total": len(tags)}


async def materials_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """创建资料库条目。"""
    body = 资料创建.model_validate(args)
    db = _获取MCP会话(context)
    created = await 创建资料(db, context.user, body)
    material = await get_material_or_404(db, context.user, str(created.id))
    return {
        "summary": f"已创建资料：{created.title or created.content_text or created.note or str(created.id)}",
        "target": {"type": "material", "id": str(created.id)},
        "undoable": True,
        "undo_tool_name": "materials.delete",
        "after": _资料快照(material),
        "data": _资料读取(created, include_asset_detail=True),
    }


async def materials_convert_to_material(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """把一条资料复制转换为新的资料库条目。"""
    body = 资料转资料库参数.model_validate(args)
    db = _获取MCP会话(context)
    source = await get_material_or_404(db, context.user, body.material_id)
    payload = 资料创建(
        type=body.type or source.type.value,
        title=body.title if body.title is not None else source.title,
        content_text=body.content_text if body.content_text is not None else source.content_text,
        note=body.note if body.note is not None else source.note,
        status=body.status,
        tags=body.tags if body.tags is not None else source.tags,
        assets=_资料附件输入(source) if body.include_assets else None,
    )
    created = await 创建资料(db, context.user, payload)
    material = await get_material_or_404(db, context.user, str(created.id))
    return {
        "summary": f"已转换为资料库条目：{created.title or created.content_text or created.note or str(created.id)}",
        "target": {"type": "material", "id": str(created.id)},
        "source": {"type": "material", "id": str(source.id)},
        "undoable": True,
        "undo_tool_name": "materials.delete",
        "after": _资料快照(material),
        "data": _资料读取(created, include_asset_detail=True),
    }


async def materials_convert_to_article(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """把一条资料转换为新文章。"""
    body = 资料转文章参数.model_validate(args)
    db = _获取MCP会话(context)
    source = await get_material_or_404(db, context.user, body.material_id)
    tag_ids = body.tag_ids
    if tag_ids is None:
        tag_ids = await _获取或创建文章标签ID(db, body.tag_names if body.tag_names is not None else (source.tags or []))
    article = await 创建文章(
        db,
        文章创建(
            title=body.title or _资料默认标题(source),
            content=body.content if body.content is not None else _资料默认正文(source, include_assets=body.include_assets),
            excerpt=body.excerpt if body.excerpt is not None else _资料默认摘要(source),
            cover_url=body.cover_url,
            status=body.status,
            category_id=body.category_id,
            tag_ids=tag_ids,
        ),
        context.user,
    )
    return {
        "summary": f"已转换为文章：{article.title}",
        "target": {"type": "article", "id": str(article.id)},
        "source": {"type": "material", "id": str(source.id)},
        "undoable": True,
        "undo_tool_name": "articles.delete",
        "after": {
            "id": str(article.id),
            "title": article.title,
            "status": article.status.value,
            "tag_ids": [str(tag.id) for tag in article.tags],
            "created_at": article.created_at.isoformat(),
        },
        "data": {
            "id": str(article.id),
            "title": article.title,
            "slug": article.slug,
            "status": article.status.value,
            "tags": [{"id": str(tag.id), "name": tag.name, "slug": tag.slug} for tag in article.tags],
        },
    }


async def materials_convert_to_todo(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """把一条资料转换为新待办。"""
    body = 资料转待办参数.model_validate(args)
    db = _获取MCP会话(context)
    source = await get_material_or_404(db, context.user, body.material_id)
    todo = await create_todo(
        db,
        context.user,
        TodoCreate(
            title=body.title or _资料默认标题(source),
            description=body.description if body.description is not None else _资料默认正文(source, include_assets=True),
            importance=body.importance,
            urgency=body.urgency,
            is_pinned=body.is_pinned,
            tags=body.tags if body.tags is not None else source.tags,
        ),
    )
    data = TodoRead.model_validate(todo).model_dump(mode="json")
    return {
        "summary": f"已转换为待办：{todo.title}",
        "target": {"type": "todo", "id": str(todo.id)},
        "source": {"type": "material", "id": str(source.id)},
        "undoable": True,
        "undo_tool_name": "todos.delete",
        "after": data,
        "data": data,
    }


async def materials_update(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """更新当前用户资料库条目。"""
    body = 资料更新参数.model_validate(args)
    db = _获取MCP会话(context)
    material = await get_material_or_404(db, context.user, body.material_id)
    校验资料更新时间(material.updated_at, body.expected_updated_at)
    before = _资料快照(material)
    updated = await 更新资料(db, context.user, body.material_id, _构建资料更新载荷(args))
    after_material = await get_material_or_404(db, context.user, body.material_id)
    return {
        "summary": f"已更新资料：{updated.title or updated.content_text or updated.note or str(updated.id)}",
        "target": {"type": "material", "id": str(updated.id)},
        "undoable": True,
        "undo_tool_name": "materials.update",
        "before": before,
        "after": _资料快照(after_material),
        "data": _资料读取(updated, include_asset_detail=True),
    }


async def materials_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """将当前用户资料库条目移入回收站。"""
    body = 资料ID参数.model_validate(args)
    db = _获取MCP会话(context)
    material = await get_material_or_404(db, context.user, body.material_id)
    before = _资料快照(material)
    summary_text = material.title or material.content_text or material.note or str(material.id)
    await 删除资料(db, context.user, body.material_id, permanent=False)
    deleted = await 获取已删资料或404(db, context.user, body.material_id)
    return {
        "summary": f"已移入回收站：{summary_text}",
        "target": {"type": "material", "id": str(deleted.id)},
        "undoable": True,
        "undo_tool_name": "materials.restore",
        "before": before,
        "after": _资料快照(deleted),
    }


async def materials_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复当前用户资料库条目。"""
    body = 资料ID参数.model_validate(args)
    db = _获取MCP会话(context)
    before_material = await 获取已删资料或404(db, context.user, body.material_id)
    before = _资料快照(before_material)
    restored = await 恢复资料(db, context.user, body.material_id)
    after_material = await get_material_or_404(db, context.user, body.material_id)
    return {
        "summary": f"已恢复资料：{restored.title or restored.content_text or restored.note or str(restored.id)}",
        "target": {"type": "material", "id": str(restored.id)},
        "undoable": True,
        "undo_tool_name": "materials.delete",
        "before": before,
        "after": _资料快照(after_material),
        "data": _资料读取(restored, include_asset_detail=True),
    }


注册工具(
    MCP工具定义(
        name="materials.list",
        description="查询当前用户资料库列表，支持状态、类型、标签、关键词和回收站筛选，列表仅返回附件关系摘要。",
        input_schema=资料列表参数.model_json_schema(),
        permission="readonly",
        handler=materials_list,
    )
)
注册工具(
    MCP工具定义(
        name="materials.get",
        description="读取当前用户的一条资料库详情，包括标签和附件关系。",
        input_schema=资料ID参数.model_json_schema(),
        permission="readonly",
        handler=materials_get,
    )
)
注册工具(
    MCP工具定义(
        name="materials.tags.list",
        description="查看当前用户资料库标签统计，可选择统计回收站标签。",
        input_schema=资料标签列表参数.model_json_schema(),
        permission="readonly",
        handler=materials_tags_list,
    )
)
注册工具(
    MCP工具定义(
        name="materials.create",
        description="为当前用户创建文本、链接、图片或文件资料，可通过撤销软删除新建资料。",
        input_schema=资料创建.model_json_schema(),
        permission="full",
        handler=materials_create,
    )
)
注册工具(
    MCP工具定义(
        name="materials.convert.to_material",
        description="把一条现有资料复制转换为新的资料库条目，默认保留标题、正文、备注、标签和附件关系。",
        input_schema=资料转资料库参数.model_json_schema(),
        permission="full",
        handler=materials_convert_to_material,
    )
)
注册工具(
    MCP工具定义(
        name="materials.convert.to_article",
        description="把一条现有资料转换为新文章，默认生成私有文章，并可沿用资料标签创建或复用文章标签。",
        input_schema=资料转文章参数.model_json_schema(),
        permission="full",
        handler=materials_convert_to_article,
    )
)
注册工具(
    MCP工具定义(
        name="materials.convert.to_todo",
        description="把一条现有资料转换为新待办，默认沿用资料标题、正文、备注和标签。",
        input_schema=资料转待办参数.model_json_schema(),
        permission="full",
        handler=materials_convert_to_todo,
    )
)
注册工具(
    MCP工具定义(
        name="materials.update",
        description="更新当前用户资料库条目的标题、正文、备注、状态、标签或附件关系，必须提供 expected_updated_at。",
        input_schema=资料更新参数.model_json_schema(),
        permission="full",
        handler=materials_update,
    )
)
注册工具(
    MCP工具定义(
        name="materials.delete",
        description="将当前用户的一条资料库条目移入回收站，不执行永久删除。",
        input_schema=资料ID参数.model_json_schema(),
        permission="full",
        handler=materials_delete,
    )
)
注册工具(
    MCP工具定义(
        name="materials.restore",
        description="从回收站恢复当前用户的一条资料库条目。",
        input_schema=资料ID参数.model_json_schema(),
        permission="full",
        handler=materials_restore,
    )
)
