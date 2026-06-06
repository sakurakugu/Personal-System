"""文件相关 MCP 工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.articles.models import 文章, 文章图片
from app.modules.files.explorer import 获取资源管理器数据, 搜索资源
from app.modules.files.folders import 构建文件夹完整路径, 列出用户文件夹
from app.modules.files.models import File, FileFolder, FilePurpose
from app.modules.files.operations import 创建文件夹, 删除文件, 删除文件夹, 移动文件, 移动文件夹, 重命名文件, 重命名文件夹
from app.modules.files.presentation import (
    构建文章图片路径,
    构建文章图片文件读取,
    构建文件读取,
    构建动态图片路径,
    构建动态图片文件读取,
    构建文娱图片路径,
    构建文娱资源文件读取,
)
from app.modules.files.schemas import FileFolderCreate, FileFolderMove, FileFolderRename, FileMove, FileRename
from app.modules.files.trash import 列出回收站资源, 恢复回收站文件夹子树, 恢复回收站文件记录
from app.modules.media.models import 文娱条目, 文娱资源
from app.modules.moments.models import 动态, 动态图片


class 文件资源管理器参数(BaseModel):
    """资源管理器读取参数。"""

    folder_id: UUID | None = Field(default=None, description="当前普通文件夹 ID，空值表示根目录")


class 文件搜索参数(BaseModel):
    """文件搜索参数。"""

    keyword: str = Field(min_length=1, max_length=120, description="搜索关键词")


class 文件元信息参数(BaseModel):
    """文件或文件夹元信息读取参数。"""

    resource_id: UUID = Field(description="资源 ID")
    resource_type: Literal["file", "folder"] = Field(description="资源类型")
    purpose: Literal["file", "article_image", "moment_image", "media_asset"] | None = Field(
        default=None,
        description="文件用途；读取文件时可指定，避免不同资源表 ID 冲突",
    )
    is_deleted: bool = Field(default=False, description="是否读取回收站中的普通文件或普通文件夹")


class 文件夹ID参数(BaseModel):
    """文件夹 ID 参数。"""

    folder_id: UUID = Field(description="普通文件夹 ID")


class 文件ID参数(BaseModel):
    """文件 ID 参数。"""

    file_id: UUID = Field(description="普通文件 ID")


class MCP文件夹创建参数(FileFolderCreate):
    """创建普通文件夹参数。"""


class MCP文件夹重命名参数(FileFolderRename):
    """重命名普通文件夹参数。"""

    folder_id: UUID = Field(description="普通文件夹 ID")
    expected_updated_at: str = Field(description="调用方读取到的 updated_at")


class MCP文件夹移动参数(FileFolderMove):
    """移动普通文件夹参数。"""

    folder_id: UUID = Field(description="普通文件夹 ID")
    expected_updated_at: str = Field(description="调用方读取到的 updated_at")


class MCP文件重命名参数(FileRename):
    """重命名普通文件参数。"""

    file_id: UUID = Field(description="普通文件 ID")
    expected_updated_at: str = Field(description="调用方读取到的 updated_at")


class MCP文件移动参数(FileMove):
    """移动普通文件参数。"""

    file_id: UUID = Field(description="普通文件 ID")
    expected_updated_at: str = Field(description="调用方读取到的 updated_at")


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


def 校验文件更新时间(actual: datetime, expected: str) -> None:
    """校验调用方读取的文件资源更新时间仍然有效。"""
    if _转UTC(actual) != _解析时间戳(expected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "文件资源已被更新，请重新读取后再修改",
                "current_updated_at": actual.isoformat(),
            },
        )


def _模型JSON(model: Any) -> dict[str, Any]:
    """将 Pydantic 模型转为稳定 JSON。"""
    return model.model_dump(mode="json")


def _文件夹快照(folder: FileFolder) -> dict[str, Any]:
    """构建普通文件夹撤销快照。"""
    return {
        "id": str(folder.id),
        "type": "folder",
        "name": folder.name,
        "parent_id": str(folder.parent_id) if folder.parent_id else None,
        "is_deleted": folder.is_deleted,
        "deleted_at": folder.deleted_at.isoformat() if folder.deleted_at else None,
        "deleted_by": str(folder.deleted_by) if folder.deleted_by else None,
        "purge_after": folder.purge_after.isoformat() if folder.purge_after else None,
        "created_at": folder.created_at.isoformat(),
        "updated_at": folder.updated_at.isoformat(),
    }


def _普通文件快照(record: File) -> dict[str, Any]:
    """构建普通文件撤销快照。"""
    return {
        "id": str(record.id),
        "type": "file",
        "purpose": record.purpose.value,
        "original_name": record.original_name,
        "folder_id": str(record.folder_id) if record.folder_id else None,
        "storage_key": record.storage_key,
        "size": record.size,
        "mime_type": record.mime_type,
        "is_deleted": record.is_deleted,
        "deleted_at": record.deleted_at.isoformat() if record.deleted_at else None,
        "deleted_by": str(record.deleted_by) if record.deleted_by else None,
        "purge_after": record.purge_after.isoformat() if record.purge_after else None,
        "purged_at": record.purged_at.isoformat() if record.purged_at else None,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


async def _读取普通文件(context: MCP调用上下文, file_id: UUID, *, is_deleted: bool = False) -> File:
    """读取当前用户普通文件。"""
    db = _获取MCP会话(context)
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == context.user.id,
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(is_deleted),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    return record


async def _读取文件夹(context: MCP调用上下文, folder_id: UUID, *, is_deleted: bool = False) -> FileFolder:
    """读取当前用户普通文件夹。"""
    db = _获取MCP会话(context)
    result = await db.execute(
        select(FileFolder).where(
            FileFolder.id == folder_id,
            FileFolder.user_id == context.user.id,
            FileFolder.is_deleted.is_(is_deleted),
        )
    )
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")
    return folder


async def _读取文章图片(context: MCP调用上下文, file_id: UUID) -> 文章图片 | None:
    """读取当前用户文章图片。"""
    db = _获取MCP会话(context)
    result = await db.execute(
        select(文章图片)
        .join(文章, 文章图片.article_id == 文章.id)
        .where(文章图片.id == file_id, 文章.author_id == context.user.id, 文章.is_deleted.is_(False))
        .options(selectinload(文章图片.article))
    )
    return result.scalar_one_or_none()


async def _读取动态图片(context: MCP调用上下文, file_id: UUID) -> 动态图片 | None:
    """读取当前用户动态图片。"""
    db = _获取MCP会话(context)
    result = await db.execute(
        select(动态图片)
        .join(动态, 动态图片.moment_id == 动态.id)
        .where(动态图片.id == file_id, 动态.user_id == context.user.id, 动态.is_deleted.is_(False))
        .options(selectinload(动态图片.moment))
    )
    return result.scalar_one_or_none()


async def _读取文娱资源(context: MCP调用上下文, file_id: UUID) -> 文娱资源 | None:
    """读取当前用户文娱资源。"""
    db = _获取MCP会话(context)
    result = await db.execute(
        select(文娱资源)
        .join(文娱条目, 文娱资源.media_item_id == 文娱条目.id)
        .where(文娱资源.id == file_id, 文娱资源.user_id == context.user.id, 文娱条目.is_deleted.is_(False))
        .options(selectinload(文娱资源.media_item))
    )
    return result.scalar_one_or_none()


async def files_explorer(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取资源管理器目录树和当前目录内容。"""
    body = 文件资源管理器参数.model_validate(args)
    data = await 获取资源管理器数据(_获取MCP会话(context), context.user, folder_id=body.folder_id)
    return _模型JSON(data)


async def files_search(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """跨普通文件、内容图片和文娱资源搜索。"""
    body = 文件搜索参数.model_validate(args)
    data = await 搜索资源(_获取MCP会话(context), context.user, keyword=body.keyword)
    return _模型JSON(data)


async def files_get_metadata(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取单个文件或文件夹元信息。"""
    body = 文件元信息参数.model_validate(args)
    db = _获取MCP会话(context)
    if body.resource_type == "folder":
        folder = await _读取文件夹(context, body.resource_id, is_deleted=body.is_deleted)
        folders = await 列出用户文件夹(db, context.user, include_deleted=True)
        folder_map = {item.id: item for item in folders}
        return {
            **_文件夹快照(folder),
            "path": 构建文件夹完整路径(folder_map, folder),
        }

    if body.purpose in (None, "file"):
        try:
            record = await _读取普通文件(context, body.resource_id, is_deleted=body.is_deleted)
        except HTTPException:
            if body.purpose == "file":
                raise
        else:
            folders = await 列出用户文件夹(db, context.user, include_deleted=True)
            folder_map = {item.id: item for item in folders}
            record_folder = folder_map.get(record.folder_id) if record.folder_id else None
            return {
                **_普通文件快照(record),
                "path": 构建文件夹完整路径(folder_map, record_folder),
                "data": _模型JSON(构建文件读取(record)),
            }

    if body.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回收站只支持普通文件和普通文件夹")
    if body.purpose in (None, "article_image") and (article_image := await _读取文章图片(context, body.resource_id)):
        data = 构建文章图片文件读取(article_image)
        return {
            **_模型JSON(data),
            "type": "file",
            "path": 构建文章图片路径(data.article_title or "未命名文章"),
            "write_policy": "readonly",
        }
    if body.purpose in (None, "moment_image") and (moment_image := await _读取动态图片(context, body.resource_id)):
        data = 构建动态图片文件读取(moment_image)
        return {
            **_模型JSON(data),
            "type": "file",
            "path": 构建动态图片路径(data.moment_title or "未命名动态"),
            "write_policy": "readonly",
        }
    if body.purpose in (None, "media_asset") and (media_asset := await _读取文娱资源(context, body.resource_id)):
        data = 构建文娱资源文件读取(media_asset)
        return {
            **_模型JSON(data),
            "type": "file",
            "path": 构建文娱图片路径(data.media_title or "未命名作品"),
            "write_policy": "readonly",
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件资源不存在")


async def files_trash_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查看普通文件和普通文件夹回收站。"""
    _ = args
    data = await 列出回收站资源(_获取MCP会话(context), context.user)
    return _模型JSON(data)


async def files_folder_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """创建普通文件夹。"""
    body = MCP文件夹创建参数.model_validate(args)
    folder = await 创建文件夹(_获取MCP会话(context), context.user, name=body.name, parent_id=body.parent_id, commit=False)
    return {
        "summary": f"已创建文件夹：{folder.name}",
        "target": {"type": "file_folder", "id": str(folder.id)},
        "undoable": True,
        "undo_tool_name": "files.folder_delete",
        "after": _文件夹快照(folder),
        "data": _文件夹快照(folder),
    }


async def files_folder_rename(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """重命名普通文件夹。"""
    body = MCP文件夹重命名参数.model_validate(args)
    before_folder = await _读取文件夹(context, body.folder_id)
    校验文件更新时间(before_folder.updated_at, body.expected_updated_at)
    before = _文件夹快照(before_folder)
    folder = await 重命名文件夹(
        _获取MCP会话(context),
        context.user,
        folder_id=body.folder_id,
        name=body.name,
        commit=False,
    )
    return {
        "summary": f"已重命名文件夹：{folder.name}",
        "target": {"type": "file_folder", "id": str(folder.id)},
        "undoable": True,
        "undo_tool_name": "files.folder_rename",
        "before": before,
        "after": _文件夹快照(folder),
        "data": _文件夹快照(folder),
    }


async def files_folder_move(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """移动普通文件夹。"""
    body = MCP文件夹移动参数.model_validate(args)
    before_folder = await _读取文件夹(context, body.folder_id)
    校验文件更新时间(before_folder.updated_at, body.expected_updated_at)
    before = _文件夹快照(before_folder)
    folder = await 移动文件夹(
        _获取MCP会话(context),
        context.user,
        folder_id=body.folder_id,
        parent_id=body.parent_id,
        commit=False,
    )
    return {
        "summary": f"已移动文件夹：{folder.name}",
        "target": {"type": "file_folder", "id": str(folder.id)},
        "undoable": True,
        "undo_tool_name": "files.folder_move",
        "before": before,
        "after": _文件夹快照(folder),
        "data": _文件夹快照(folder),
    }


async def files_folder_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """将普通文件夹移入回收站。"""
    body = 文件夹ID参数.model_validate(args)
    before_folder = await _读取文件夹(context, body.folder_id)
    before = _文件夹快照(before_folder)
    await 删除文件夹(_获取MCP会话(context), context.user, folder_id=body.folder_id, commit=False)
    deleted = await _读取文件夹(context, body.folder_id, is_deleted=True)
    return {
        "summary": f"已移入回收站：{before_folder.name}",
        "target": {"type": "file_folder", "id": str(deleted.id)},
        "undoable": True,
        "undo_tool_name": "files.folder_restore",
        "before": before,
        "after": _文件夹快照(deleted),
    }


async def files_folder_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复普通文件夹。"""
    body = 文件夹ID参数.model_validate(args)
    before_folder = await _读取文件夹(context, body.folder_id, is_deleted=True)
    before = _文件夹快照(before_folder)
    await 恢复回收站文件夹子树(_获取MCP会话(context), context.user, body.folder_id, commit=False)
    restored = await _读取文件夹(context, body.folder_id)
    return {
        "summary": f"已恢复文件夹：{restored.name}",
        "target": {"type": "file_folder", "id": str(restored.id)},
        "undoable": True,
        "undo_tool_name": "files.folder_delete",
        "before": before,
        "after": _文件夹快照(restored),
        "data": _文件夹快照(restored),
    }


async def files_rename(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """重命名普通文件。"""
    body = MCP文件重命名参数.model_validate(args)
    before_record = await _读取普通文件(context, body.file_id)
    校验文件更新时间(before_record.updated_at, body.expected_updated_at)
    before = _普通文件快照(before_record)
    data = await 重命名文件(
        _获取MCP会话(context),
        context.user,
        file_id=body.file_id,
        original_name=body.original_name,
        commit=False,
    )
    after_record = await _读取普通文件(context, body.file_id)
    return {
        "summary": f"已重命名文件：{data.original_name}",
        "target": {"type": "file", "id": str(data.id)},
        "undoable": True,
        "undo_tool_name": "files.rename",
        "before": before,
        "after": _普通文件快照(after_record),
        "data": _模型JSON(data),
    }


async def files_move(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """移动普通文件。"""
    body = MCP文件移动参数.model_validate(args)
    before_record = await _读取普通文件(context, body.file_id)
    校验文件更新时间(before_record.updated_at, body.expected_updated_at)
    before = _普通文件快照(before_record)
    data = await 移动文件(
        _获取MCP会话(context),
        context.user,
        file_id=body.file_id,
        folder_id=body.folder_id,
        commit=False,
    )
    after_record = await _读取普通文件(context, body.file_id)
    return {
        "summary": f"已移动文件：{data.original_name}",
        "target": {"type": "file", "id": str(data.id)},
        "undoable": True,
        "undo_tool_name": "files.move",
        "before": before,
        "after": _普通文件快照(after_record),
        "data": _模型JSON(data),
    }


async def files_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """将普通文件移入回收站。"""
    body = 文件ID参数.model_validate(args)
    before_record = await _读取普通文件(context, body.file_id)
    before = _普通文件快照(before_record)
    await 删除文件(_获取MCP会话(context), context.user, body.file_id, commit=False)
    deleted = await _读取普通文件(context, body.file_id, is_deleted=True)
    return {
        "summary": f"已移入回收站：{before_record.original_name}",
        "target": {"type": "file", "id": str(deleted.id)},
        "undoable": True,
        "undo_tool_name": "files.restore",
        "before": before,
        "after": _普通文件快照(deleted),
    }


async def files_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复普通文件。"""
    body = 文件ID参数.model_validate(args)
    before_record = await _读取普通文件(context, body.file_id, is_deleted=True)
    before = _普通文件快照(before_record)
    await 恢复回收站文件记录(_获取MCP会话(context), context.user, body.file_id, commit=False)
    restored = await _读取普通文件(context, body.file_id)
    return {
        "summary": f"已恢复文件：{restored.original_name}",
        "target": {"type": "file", "id": str(restored.id)},
        "undoable": True,
        "undo_tool_name": "files.delete",
        "before": before,
        "after": _普通文件快照(restored),
        "data": _模型JSON(构建文件读取(restored)),
    }


注册工具(
    MCP工具定义(
        name="files.explorer",
        description="读取资源管理器目录树、当前目录普通文件夹和文件；根目录包含文章图片、动态图片和文娱资源。",
        input_schema=文件资源管理器参数.model_json_schema(),
        permission="readonly",
        handler=files_explorer,
    )
)
注册工具(
    MCP工具定义(
        name="files.search",
        description="跨普通文件、文件夹、文章图片、动态图片和文娱资源搜索。",
        input_schema=文件搜索参数.model_json_schema(),
        permission="readonly",
        handler=files_search,
    )
)
注册工具(
    MCP工具定义(
        name="files.get_metadata",
        description="读取单个文件或文件夹元信息、路径、大小、MIME 和所属业务对象。",
        input_schema=文件元信息参数.model_json_schema(),
        permission="readonly",
        handler=files_get_metadata,
    )
)
注册工具(
    MCP工具定义(
        name="files.trash_list",
        description="查看普通文件和普通文件夹回收站。",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        permission="readonly",
        handler=files_trash_list,
    )
)
注册工具(
    MCP工具定义(
        name="files.folder_create",
        description="创建普通文件夹。",
        input_schema=MCP文件夹创建参数.model_json_schema(),
        permission="full",
        handler=files_folder_create,
    )
)
注册工具(
    MCP工具定义(
        name="files.folder_rename",
        description="重命名普通文件夹，必须提供 expected_updated_at。",
        input_schema=MCP文件夹重命名参数.model_json_schema(),
        permission="full",
        handler=files_folder_rename,
    )
)
注册工具(
    MCP工具定义(
        name="files.folder_move",
        description="移动普通文件夹，必须提供 expected_updated_at。",
        input_schema=MCP文件夹移动参数.model_json_schema(),
        permission="full",
        handler=files_folder_move,
    )
)
注册工具(
    MCP工具定义(
        name="files.folder_delete",
        description="将普通文件夹移入回收站，不执行永久删除。",
        input_schema=文件夹ID参数.model_json_schema(),
        permission="full",
        handler=files_folder_delete,
    )
)
注册工具(
    MCP工具定义(
        name="files.folder_restore",
        description="从回收站恢复普通文件夹。",
        input_schema=文件夹ID参数.model_json_schema(),
        permission="full",
        handler=files_folder_restore,
    )
)
注册工具(
    MCP工具定义(
        name="files.rename",
        description="重命名普通文件，必须提供 expected_updated_at；文章图片、动态图片和文娱资源保持只读。",
        input_schema=MCP文件重命名参数.model_json_schema(),
        permission="full",
        handler=files_rename,
    )
)
注册工具(
    MCP工具定义(
        name="files.move",
        description="移动普通文件到目标普通文件夹，必须提供 expected_updated_at。",
        input_schema=MCP文件移动参数.model_json_schema(),
        permission="full",
        handler=files_move,
    )
)
注册工具(
    MCP工具定义(
        name="files.delete",
        description="将普通文件移入回收站，不执行永久删除。",
        input_schema=文件ID参数.model_json_schema(),
        permission="full",
        handler=files_delete,
    )
)
注册工具(
    MCP工具定义(
        name="files.restore",
        description="从回收站恢复普通文件。",
        input_schema=文件ID参数.model_json_schema(),
        permission="full",
        handler=files_restore,
    )
)
