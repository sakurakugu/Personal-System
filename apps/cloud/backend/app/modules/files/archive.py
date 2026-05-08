"""文件归档辅助。"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import PurePosixPath
import zipfile
from uuid import UUID

from app.modules.articles.models import ArticleImage
from app.modules.files.folders import 构建文件夹谱系
from app.modules.files.models import File, FileFolder
from app.modules.moments.models import MomentImage
from app.shared.storage.client import 获取对象字节

默认普通文件名 = "file"
文章图片目录名称 = "文章图片"
动态图片目录名称 = "动态图片"


@dataclass(frozen=True)
class ArchiveEntry:
    """压缩包中的文件条目。"""

    id: UUID
    original_name: str
    storage_key: str
    archive_parts: list[str]


def 构建归档文件路径(parts: list[str], filename: str) -> str:
    """构造压缩包中的文件路径。"""
    normalized_parts = [part.strip() for part in parts if part.strip()]
    normalized_filename = filename.strip()
    if not normalized_parts and not normalized_filename:
        return ""
    if not normalized_filename:
        return str(PurePosixPath(*normalized_parts))
    if not normalized_parts:
        return normalized_filename
    return str(PurePosixPath(*normalized_parts, normalized_filename))


def 确保归档路径唯一(used_paths: set[str], candidate: str) -> str:
    """确保压缩包内路径唯一。"""
    if candidate not in used_paths:
        used_paths.add(candidate)
        return candidate

    path = PurePosixPath(candidate)
    suffix = path.suffix
    stem = path.stem if suffix else path.name
    parent = path.parent if str(path.parent) != "." else PurePosixPath()
    index = 2
    while True:
        next_name = f"{stem} ({index}){suffix}"
        next_path = str(parent / next_name) if str(parent) != "." else next_name
        if next_path not in used_paths:
            used_paths.add(next_path)
            return next_path
        index += 1


def 收集子孙文件夹ID(folder_map: dict[UUID, FileFolder], folder_ids: set[UUID]) -> set[UUID]:
    """收集选中文件夹下的全部后代文件夹。"""
    descendants = set(folder_ids)
    changed = True
    while changed:
        changed = False
        for folder in folder_map.values():
            if folder.parent_id in descendants and folder.id not in descendants:
                descendants.add(folder.id)
                changed = True
    return descendants


def 构建归档根名称映射(selected_folders: list[FileFolder]) -> dict[UUID, str]:
    """为选中文件夹分配压缩包根目录名。"""
    used_names: set[str] = set()
    root_name_map: dict[UUID, str] = {}
    for folder in selected_folders:
        root_name_map[folder.id] = 确保归档路径唯一(used_names, folder.name.strip() or 默认普通文件名)
    return root_name_map


def 构建常规文件归档路径(
    record: File,
    *,
    descendant_folder_ids: set[UUID],
    archive_root_name_map: dict[UUID, str],
    folder_map: dict[UUID, FileFolder],
) -> list[str]:
    """构造普通文件在压缩包中的路径前缀。"""
    if record.folder_id in archive_root_name_map:
        return [archive_root_name_map[record.folder_id]]
    if record.folder_id in descendant_folder_ids:
        lineage = 构建文件夹谱系(folder_map, folder_map[record.folder_id])
        root_folder = next((item for item in lineage if item.id in archive_root_name_map), None)
        if root_folder is None:
            return []
        return [
            archive_root_name_map[root_folder.id],
            *[item.name for item in lineage if item.id != root_folder.id],
        ]
    if record.folder_id is None:
        return []
    lineage = 构建文件夹谱系(folder_map, folder_map[record.folder_id])
    return [item.name for item in lineage]


def 构建文章图片归档路径(record: ArticleImage) -> list[str]:
    """构造文章图片在压缩包中的路径前缀。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return [文章图片目录名称, article_title.strip() or "未命名文章"]


def 构建动态图片归档路径(record: MomentImage) -> list[str]:
    """构造动态图片在压缩包中的路径前缀。"""
    moment_title = record.moment.title if record.moment is not None and record.moment.title is not None else "未命名动态"
    return [动态图片目录名称, moment_title.strip() or "未命名动态"]


def 构建归档字节(
    *,
    selected_root_folders: list[FileFolder],
    descendant_folder_ids: set[UUID],
    folder_map: dict[UUID, FileFolder],
    archive_root_name_map: dict[UUID, str],
    archive_entries: list[ArchiveEntry],
) -> bytes:
    """构造最终的 ZIP 二进制内容。"""
    output = io.BytesIO()
    used_archive_paths: set[str] = set()
    used_archive_folder_paths: set[str] = set()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for folder in selected_root_folders:
            archive_path = archive_root_name_map[folder.id]
            if archive_path not in used_archive_folder_paths:
                used_archive_folder_paths.add(archive_path)
                archive.writestr(f"{archive_path}/", b"")

        for folder_id in descendant_folder_ids:
            folder = folder_map[folder_id]
            lineage = 构建文件夹谱系(folder_map, folder)
            root_folder = next((item for item in lineage if item.id in archive_root_name_map), None)
            if root_folder is None:
                continue
            relative_parts = [item.name for item in lineage if item.id != root_folder.id]
            archive_folder_path = 构建归档文件路径([archive_root_name_map[root_folder.id], *relative_parts], "")
            if archive_folder_path and archive_folder_path not in used_archive_folder_paths:
                used_archive_folder_paths.add(archive_folder_path)
                archive.writestr(f"{archive_folder_path}/", b"")

        for entry in archive_entries:
            for index in range(1, len(entry.archive_parts) + 1):
                archive_folder_path = 构建归档文件路径(entry.archive_parts[:index], "")
                if archive_folder_path and archive_folder_path not in used_archive_folder_paths:
                    used_archive_folder_paths.add(archive_folder_path)
                    archive.writestr(f"{archive_folder_path}/", b"")

        for entry in archive_entries:
            archive_path = 确保归档路径唯一(
                used_archive_paths,
                构建归档文件路径(entry.archive_parts, entry.original_name),
            )
            content, _ = 获取对象字节(entry.storage_key)
            archive.writestr(archive_path, content)

    return output.getvalue()
