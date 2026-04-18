"""文件归档兼容入口。"""

from app.modules.files.archive import (
    ArchiveEntry,
    build_archive_bytes,
    build_archive_file_path,
    build_archive_root_name_map,
    build_article_image_archive_parts,
    build_regular_file_archive_parts,
    collect_descendant_folder_ids,
    ensure_unique_archive_path,
)

__all__ = [
    "ArchiveEntry",
    "build_archive_bytes",
    "build_archive_file_path",
    "build_archive_root_name_map",
    "build_article_image_archive_parts",
    "build_regular_file_archive_parts",
    "collect_descendant_folder_ids",
    "ensure_unique_archive_path",
]
