"""文件资源管理相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.file import FilePurpose


def normalize_folder_name(value: str) -> str:
    """规范化文件夹名称。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("文件夹名称不能为空")
    if normalized in {".", ".."}:
        raise ValueError("文件夹名称不合法")
    if "/" in normalized or "\\" in normalized:
        raise ValueError("文件夹名称不能包含斜杠")
    return normalized


def normalize_file_name(value: str) -> str:
    """规范化文件名称。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("文件名称不能为空")
    if normalized in {".", ".."}:
        raise ValueError("文件名称不合法")
    if "/" in normalized or "\\" in normalized:
        raise ValueError("文件名称不能包含斜杠")
    return normalized


class FileRead(BaseModel):
    """文件数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    folder_id: UUID | None
    purpose: FilePurpose
    original_name: str
    url: str
    size: int
    mime_type: str
    created_at: datetime
    article_id: UUID | None = None
    article_title: str | None = None


class FileFolderRead(BaseModel):
    """文件夹数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    name: str
    created_at: datetime
    updated_at: datetime


class FileFolderTreeNodeRead(BaseModel):
    """文件夹树节点。"""

    id: UUID
    parent_id: UUID | None
    name: str
    children: list["FileFolderTreeNodeRead"] = Field(default_factory=list)


class FileBreadcrumbRead(BaseModel):
    """文件夹面包屑。"""

    id: UUID | None
    name: str


class FileExplorerRead(BaseModel):
    """资源管理器数据响应。"""

    current_folder: FileFolderRead | None
    breadcrumbs: list[FileBreadcrumbRead]
    tree: list[FileFolderTreeNodeRead]
    folders: list[FileFolderRead]
    files: list[FileRead]


class FileFolderSearchRead(BaseModel):
    """文件夹搜索结果。"""

    id: UUID
    parent_id: UUID | None
    name: str
    path: str
    updated_at: datetime


class FileSearchItemRead(BaseModel):
    """文件搜索结果。"""

    id: UUID
    folder_id: UUID | None
    purpose: FilePurpose
    original_name: str
    url: str
    size: int
    mime_type: str
    created_at: datetime
    path: str
    article_id: UUID | None = None
    article_title: str | None = None


class FileSearchRead(BaseModel):
    """跨目录搜索结果。"""

    folders: list[FileFolderSearchRead]
    files: list[FileSearchItemRead]


class FileFolderCreate(BaseModel):
    """创建文件夹请求。"""

    name: str = Field(max_length=120)
    parent_id: UUID | None = None

    _normalize_name = field_validator("name")(normalize_folder_name)


class FileFolderRename(BaseModel):
    """重命名文件夹请求。"""

    name: str = Field(max_length=120)

    _normalize_name = field_validator("name")(normalize_folder_name)


class FileFolderMove(BaseModel):
    """移动文件夹请求。"""

    parent_id: UUID | None = None


class FileMove(BaseModel):
    """移动文件请求。"""

    folder_id: UUID | None = None


class FileRename(BaseModel):
    """重命名文件请求。"""

    original_name: str = Field(max_length=500)

    _normalize_name = field_validator("original_name")(normalize_file_name)


class FileArchiveRequest(BaseModel):
    """打包下载请求。"""

    folder_ids: list[UUID] = Field(default_factory=list)
    file_ids: list[UUID] = Field(default_factory=list)
    archive_name: str | None = Field(default=None, max_length=200)

    @field_validator("archive_name")
    @classmethod
    def validate_archive_name(cls, value: str | None) -> str | None:
        """校验压缩包文件名。"""
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            return None
        if "/" in normalized or "\\" in normalized:
            raise ValueError("压缩包名称不能包含斜杠")
        return normalized


FileFolderTreeNodeRead.model_rebuild()
