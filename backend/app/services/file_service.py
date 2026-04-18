"""文件服务兼容入口。"""

from __future__ import annotations

from app.modules.files import archive as archive_module
from app.modules.files import explorer as explorer_module
from app.modules.files import operations as operations_module
from app.modules.files.archive import build_archive_file_path
from app.modules.files.folders import (
    build_folder_breadcrumbs,
    build_folder_full_path,
    build_folder_tree_nodes,
    list_user_folders,
)
from app.modules.files.operations import rename_file
from app.modules.files.upload_preparation import normalize_filename_for_content_type, prepare_upload_payload
from app.services.storage_service import fetch_object_bytes


async def search_resources(db, user, *, keyword: str):
    """按关键词跨目录搜索资源。"""
    original_list_user_folders = explorer_module.list_user_folders
    explorer_module.list_user_folders = list_user_folders
    try:
        return await explorer_module.search_resources(db, user, keyword=keyword)
    finally:
        explorer_module.list_user_folders = original_list_user_folders


async def build_archive_payload(
    db,
    user,
    *,
    folder_ids,
    file_ids,
):
    """构造打包下载的 ZIP 内容。"""
    original_list_user_folders = operations_module.list_user_folders
    original_fetch_object_bytes = archive_module.fetch_object_bytes
    operations_module.list_user_folders = list_user_folders
    archive_module.fetch_object_bytes = fetch_object_bytes
    try:
        return await operations_module.build_archive_payload(
            db,
            user,
            folder_ids=folder_ids,
            file_ids=file_ids,
        )
    finally:
        operations_module.list_user_folders = original_list_user_folders
        archive_module.fetch_object_bytes = original_fetch_object_bytes


__all__ = [
    "build_archive_file_path",
    "build_archive_payload",
    "build_folder_breadcrumbs",
    "build_folder_full_path",
    "build_folder_tree_nodes",
    "fetch_object_bytes",
    "list_user_folders",
    "normalize_filename_for_content_type",
    "prepare_upload_payload",
    "rename_file",
    "search_resources",
]
