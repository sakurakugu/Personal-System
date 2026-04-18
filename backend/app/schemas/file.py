"""文件 Schema 兼容入口。"""

from app.modules.files.schemas import (
    FileArchiveRequest,
    FileBreadcrumbRead,
    FileExplorerRead,
    FileFolderCreate,
    FileFolderMove,
    FileFolderRead,
    FileFolderRename,
    FileFolderSearchRead,
    FileFolderTreeNodeRead,
    FileMove,
    FileRead,
    FileRename,
    FileSearchItemRead,
    FileSearchRead,
    normalize_file_name,
    normalize_folder_name,
)

__all__ = [
    "FileArchiveRequest",
    "FileBreadcrumbRead",
    "FileExplorerRead",
    "FileFolderCreate",
    "FileFolderMove",
    "FileFolderRead",
    "FileFolderRename",
    "FileFolderSearchRead",
    "FileFolderTreeNodeRead",
    "FileMove",
    "FileRead",
    "FileRename",
    "FileSearchItemRead",
    "FileSearchRead",
    "normalize_file_name",
    "normalize_folder_name",
]
