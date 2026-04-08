"""文件资源管理服务。"""

from __future__ import annotations

import io
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import zipfile
from uuid import UUID

from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException, UploadFile
import pillow_avif  # noqa: F401
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleImage
from app.models.file import File, FileFolder, FilePurpose
from app.models.user import User
from app.schemas.file import (
    FileBreadcrumbRead,
    FileExplorerRead,
    FileFolderRead,
    FileFolderSearchRead,
    FileFolderTreeNodeRead,
    FileRead,
    FileSearchItemRead,
    FileSearchRead,
)
from app.services.storage_service import (
    build_public_url,
    build_storage_key,
    fetch_object_bytes,
    remove_object_best_effort,
    upload_bytes,
)

最大上传字节数 = 10 * 1024 * 1024
AVIF质量 = 60
默认图片文件名 = "image"
默认普通文件名 = "file"
根目录名称 = "全部文件"
文章图片目录名称 = "文章图片"
普通文件存储目录 = "files"
文章图片存储目录 = "articles"
图片扩展名 = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}
扩展名到媒体类型映射 = {
    ".avif": "image/avif",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".ico": "image/x-icon",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
    ".zip": "application/zip",
}


@dataclass(frozen=True)
class PreparedUpload:
    """规范化后的上传内容。"""

    original_name: str
    storage_name: str
    content: bytes
    content_type: str


@dataclass(frozen=True)
class ArchiveEntry:
    """压缩包中的文件条目。"""

    id: UUID
    original_name: str
    storage_key: str
    archive_parts: list[str]


def normalize_content_type(content_type: str) -> str:
    """规范化媒体类型字符串。"""
    normalized = content_type.strip().lower()
    if normalized == "image/jpg":
        return "image/jpeg"
    return normalized


def guess_extension(filename: str, content_type: str) -> str:
    """优先从文件名，其次从媒体类型推断扩展名。"""
    suffix = Path(filename).suffix.strip().lower()
    if suffix:
        return suffix

    normalized_content_type = normalize_content_type(content_type)
    for ext, mapped_content_type in 扩展名到媒体类型映射.items():
        if mapped_content_type == normalized_content_type:
            return ext
    return ""


def guess_content_type(content_type: str, filename: str) -> str:
    """优先使用上传声明的媒体类型，其次从扩展名推断。"""
    normalized_content_type = normalize_content_type(content_type)
    if normalized_content_type:
        return normalized_content_type

    return 扩展名到媒体类型映射.get(guess_extension(filename, normalized_content_type), "application/octet-stream")


def build_fallback_filename(filename: str, content_type: str) -> str:
    """为空文件名生成兜底名称。"""
    stripped_filename = filename.strip()
    if stripped_filename:
        return stripped_filename

    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    stem = 默认图片文件名 if normalized_content_type.startswith("image/") else 默认普通文件名
    return f"{stem}{ext}" if ext else stem


def normalize_filename_for_content_type(filename: str, content_type: str) -> str:
    """让展示文件名与真实内容类型保持一致。"""
    fallback_filename = build_fallback_filename(filename, content_type)
    normalized_content_type = guess_content_type(content_type, fallback_filename)
    if normalized_content_type == "image/avif":
        return build_target_filename(fallback_filename, ".avif")
    return fallback_filename


def build_target_filename(source_filename: str, target_ext: str) -> str:
    """基于原始名称生成目标格式文件名。"""
    fallback_filename = build_fallback_filename(source_filename, "")
    stem = Path(fallback_filename).stem.strip()
    if not stem or stem == ".":
        stem = 默认图片文件名
    return f"{stem}{target_ext}"


def is_image_upload(filename: str, content_type: str) -> bool:
    """根据扩展名与媒体类型判断是否为图片。"""
    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    return normalized_content_type.startswith("image/") or ext in 图片扩展名


def is_svg_upload(filename: str, content_type: str) -> bool:
    """判断是否为 SVG 矢量图。"""
    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    return ext == ".svg" or normalized_content_type == "image/svg+xml"


def is_avif_upload(filename: str, content_type: str) -> bool:
    """判断是否已经是 AVIF。"""
    ext = guess_extension(filename, content_type)
    normalized_content_type = guess_content_type(content_type, filename)
    return ext == ".avif" or normalized_content_type == "image/avif"


def is_animated_image(image: Image.Image) -> bool:
    """判断图片是否包含多帧动画。"""
    return bool(getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1)


def convert_image_to_avif(content: bytes) -> bytes:
    """将静态位图转换为 AVIF。"""
    with Image.open(io.BytesIO(content)) as image:
        normalized_image = ImageOps.exif_transpose(image)

        if (
            normalized_image.mode in {"RGBA", "LA"}
            or (normalized_image.mode == "P" and "transparency" in normalized_image.info)
        ):
            normalized_image = normalized_image.convert("RGBA")
        else:
            normalized_image = normalized_image.convert("RGB")

        output = io.BytesIO()
        normalized_image.save(output, format="AVIF", quality=AVIF质量)
        return output.getvalue()


def prepare_upload_payload(
    filename: str,
    content_type: str,
    content: bytes,
    *,
    compress_static_images: bool,
) -> PreparedUpload:
    """将上传内容规范化为最终存储格式。"""
    resolved_content_type = guess_content_type(content_type, filename)
    resolved_filename = normalize_filename_for_content_type(filename, resolved_content_type)

    if not is_image_upload(resolved_filename, resolved_content_type):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    if not compress_static_images:
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    if is_svg_upload(resolved_filename, resolved_content_type) or is_avif_upload(
        resolved_filename, resolved_content_type
    ):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    try:
        with Image.open(io.BytesIO(content)) as image:
            if is_animated_image(image):
                return PreparedUpload(
                    original_name=resolved_filename,
                    storage_name=resolved_filename,
                    content=content,
                    content_type=resolved_content_type,
                )
    except (UnidentifiedImageError, OSError, ValueError):
        return PreparedUpload(
            original_name=resolved_filename,
            storage_name=resolved_filename,
            content=content,
            content_type=resolved_content_type,
        )

    converted_content = convert_image_to_avif(content)
    converted_filename = normalize_filename_for_content_type(resolved_filename, "image/avif")
    return PreparedUpload(
        original_name=converted_filename,
        storage_name=converted_filename,
        content=converted_content,
        content_type="image/avif",
    )


def build_folder_tree_nodes(folders: list[FileFolder]) -> list[FileFolderTreeNodeRead]:
    """构造文件夹树。"""
    children_map: dict[UUID | None, list[FileFolder]] = defaultdict(list)
    for folder in folders:
        children_map[folder.parent_id].append(folder)

    def build_nodes(parent_id: UUID | None) -> list[FileFolderTreeNodeRead]:
        return [
            FileFolderTreeNodeRead(
                id=folder.id,
                parent_id=folder.parent_id,
                name=folder.name,
                children=build_nodes(folder.id),
            )
            for folder in children_map.get(parent_id, [])
        ]

    return build_nodes(None)


def build_folder_breadcrumbs(
    folder_map: dict[UUID, FileFolder],
    current_folder: FileFolder | None,
) -> list[FileBreadcrumbRead]:
    """构造当前目录的面包屑。"""
    breadcrumbs = [FileBreadcrumbRead(id=None, name="全部文件")]
    if current_folder is None:
        return breadcrumbs

    current_path: list[FileBreadcrumbRead] = []
    cursor: FileFolder | None = current_folder
    while cursor is not None:
        current_path.append(FileBreadcrumbRead(id=cursor.id, name=cursor.name))
        cursor = folder_map.get(cursor.parent_id) if cursor.parent_id is not None else None

    breadcrumbs.extend(reversed(current_path))
    return breadcrumbs


def build_folder_full_path(folder_map: dict[UUID, FileFolder], folder: FileFolder | None) -> str:
    """构造文件夹完整路径。"""
    if folder is None:
        return 根目录名称

    parts = [item.name for item in build_folder_lineage(folder_map, folder)]
    return " / ".join([根目录名称, *parts])


def build_folder_lineage(folder_map: dict[UUID, FileFolder], folder: FileFolder) -> list[FileFolder]:
    """返回从根到当前文件夹的路径。"""
    lineage: list[FileFolder] = []
    cursor: FileFolder | None = folder
    while cursor is not None:
        lineage.append(cursor)
        cursor = folder_map.get(cursor.parent_id) if cursor.parent_id is not None else None
    return list(reversed(lineage))


def build_archive_file_path(parts: list[str], filename: str) -> str:
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


def ensure_unique_archive_path(used_paths: set[str], candidate: str) -> str:
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


def build_article_image_path(article_title: str) -> str:
    """构造文章图片在资源管理器中的展示路径。"""
    normalized_title = article_title.strip() or "未命名文章"
    return " / ".join([根目录名称, 文章图片目录名称, normalized_title])


def build_file_read(record: File) -> FileRead:
    """将普通文件模型转换为统一的文件响应。"""
    return FileRead(
        id=record.id,
        folder_id=record.folder_id,
        purpose=record.purpose,
        original_name=record.original_name,
        url=build_public_url(record.storage_key),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
    )


def build_article_image_file_read(record: ArticleImage) -> FileRead:
    """将文章图片模型转换为统一的文件响应。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return FileRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=record.original_name,
        url=build_public_url(record.storage_key),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        article_id=record.article_id,
        article_title=article_title,
    )


def build_search_file_read(record: File, *, path: str) -> FileSearchItemRead:
    """将普通文件模型转换为搜索结果项。"""
    return FileSearchItemRead(
        id=record.id,
        folder_id=record.folder_id,
        purpose=record.purpose,
        original_name=record.original_name,
        url=build_public_url(record.storage_key),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=path,
    )


def build_article_image_search_read(record: ArticleImage) -> FileSearchItemRead:
    """将文章图片模型转换为搜索结果项。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return FileSearchItemRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=record.original_name,
        url=build_public_url(record.storage_key),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=build_article_image_path(article_title),
        article_id=record.article_id,
        article_title=article_title,
    )


def sort_explorer_files(records: list[FileRead]) -> list[FileRead]:
    """统一排序普通文件与文章图片。"""
    return sorted(records, key=lambda item: (item.original_name.lower(), -item.created_at.timestamp()))


def folder_scope_query(query: Select[tuple[FileFolder]], parent_id: UUID | None) -> Select[tuple[FileFolder]]:
    """为文件夹查询追加父级范围。"""
    if parent_id is None:
        return query.where(FileFolder.parent_id.is_(None))
    return query.where(FileFolder.parent_id == parent_id)


def file_scope_query(query: Select[tuple[File]], folder_id: UUID | None) -> Select[tuple[File]]:
    """为文件查询追加目录范围。"""
    if folder_id is None:
        return query.where(File.folder_id.is_(None))
    return query.where(File.folder_id == folder_id)


async def get_folder_or_404(db: AsyncSession, user: User, folder_id: UUID) -> FileFolder:
    """读取当前用户的文件夹。"""
    result = await db.execute(select(FileFolder).where(FileFolder.id == folder_id, FileFolder.user_id == user.id))
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    return folder


async def list_user_folders(db: AsyncSession, user: User) -> list[FileFolder]:
    """读取当前用户的全部文件夹。"""
    result = await db.execute(
        select(FileFolder)
        .where(FileFolder.user_id == user.id)
        .order_by(FileFolder.parent_id.asc().nullsfirst(), func.lower(FileFolder.name), FileFolder.created_at.asc())
    )
    return list(result.scalars().all())


async def ensure_unique_folder_name(
    db: AsyncSession,
    user: User,
    *,
    name: str,
    parent_id: UUID | None,
    exclude_folder_id: UUID | None = None,
) -> None:
    """校验同级目录下文件夹名称唯一。"""
    query = folder_scope_query(
        select(FileFolder).where(
            FileFolder.user_id == user.id,
            func.lower(FileFolder.name) == name.lower(),
        ),
        parent_id,
    )
    if exclude_folder_id is not None:
        query = query.where(FileFolder.id != exclude_folder_id)

    result = await db.execute(query.limit(1))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="同级目录下已存在同名文件夹")


async def ensure_folder_move_allowed(
    db: AsyncSession,
    user: User,
    *,
    folder: FileFolder,
    parent_id: UUID | None,
) -> None:
    """校验文件夹移动目标是否合法。"""
    if parent_id is None or parent_id == folder.parent_id:
        return

    if parent_id == folder.id:
        raise HTTPException(status_code=400, detail="文件夹不能移动到自身内")

    folder_map = {item.id: item for item in await list_user_folders(db, user)}
    target_folder = folder_map.get(parent_id)
    if target_folder is None:
        raise HTTPException(status_code=404, detail="目标文件夹不存在")

    cursor: FileFolder | None = target_folder
    while cursor is not None:
        if cursor.id == folder.id:
            raise HTTPException(status_code=400, detail="文件夹不能移动到自己的子目录中")
        cursor = folder_map.get(cursor.parent_id) if cursor.parent_id is not None else None


def resolve_storage_directory(purpose: FilePurpose) -> str:
    """根据文件用途返回对象存储目录。"""
    if purpose is FilePurpose.article_image:
        return 文章图片存储目录
    return 普通文件存储目录


def should_compress_static_images(purpose: FilePurpose) -> bool:
    """根据文件用途判断是否压缩静态位图。"""
    return purpose is FilePurpose.article_image


def validate_upload_purpose(filename: str, content_type: str, purpose: FilePurpose) -> None:
    """校验上传内容是否符合用途约束。"""
    if purpose is FilePurpose.article_image and not is_image_upload(filename, content_type):
        raise HTTPException(status_code=400, detail="文章图片只允许上传图片文件")


async def get_explorer_data(
    db: AsyncSession,
    user: User,
    *,
    folder_id: UUID | None,
) -> FileExplorerRead:
    """读取资源管理器所需的目录树与当前目录内容。"""
    folders = await list_user_folders(db, user)
    folder_map = {folder.id: folder for folder in folders}
    current_folder = folder_map.get(folder_id) if folder_id is not None else None
    if folder_id is not None and current_folder is None:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    child_folders = [folder for folder in folders if folder.parent_id == folder_id]
    file_result = await db.execute(
        file_scope_query(
            select(File)
            .where(File.user_id == user.id, File.purpose == FilePurpose.file)
            .order_by(func.lower(File.original_name), File.created_at.desc()),
            folder_id,
        )
    )
    file_records = list(file_result.scalars().all())
    explorer_files = [build_file_read(record) for record in file_records]
    if folder_id is None:
        article_image_result = await db.execute(
            select(ArticleImage)
            .join(Article, ArticleImage.article_id == Article.id)
            .where(Article.author_id == user.id)
            .options(selectinload(ArticleImage.article))
            .order_by(func.lower(ArticleImage.original_name), ArticleImage.created_at.desc())
        )
        article_image_records = list(article_image_result.scalars().all())
        explorer_files.extend(build_article_image_file_read(record) for record in article_image_records)

    return FileExplorerRead(
        current_folder=FileFolderRead.model_validate(current_folder) if current_folder is not None else None,
        breadcrumbs=build_folder_breadcrumbs(folder_map, current_folder),
        tree=build_folder_tree_nodes(folders),
        folders=[FileFolderRead.model_validate(folder) for folder in child_folders],
        files=sort_explorer_files(explorer_files),
    )


async def search_resources(
    db: AsyncSession,
    user: User,
    *,
    keyword: str,
) -> FileSearchRead:
    """按关键词跨目录搜索文件夹与文件。"""
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return FileSearchRead(folders=[], files=[])

    folders = await list_user_folders(db, user)
    folder_map = {folder.id: folder for folder in folders}

    matched_folders = [
        FileFolderSearchRead(
            id=folder.id,
            parent_id=folder.parent_id,
            name=folder.name,
            path=build_folder_full_path(folder_map, folder),
            updated_at=folder.updated_at,
        )
        for folder in folders
        if normalized_keyword in folder.name.lower()
    ]

    file_result = await db.execute(
        select(File)
        .where(
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            func.lower(File.original_name).contains(normalized_keyword),
        )
        .order_by(File.created_at.desc())
    )
    file_records = list(file_result.scalars().all())
    matched_files = [
        build_search_file_read(
            record,
            path=build_folder_full_path(folder_map, folder_map.get(record.folder_id) if record.folder_id else None),
        )
        for record in file_records
    ]
    article_image_result = await db.execute(
        select(ArticleImage)
        .join(Article, ArticleImage.article_id == Article.id)
        .where(
            Article.author_id == user.id,
            or_(
                func.lower(ArticleImage.original_name).contains(normalized_keyword),
                func.lower(Article.title).contains(normalized_keyword),
            ),
        )
        .options(selectinload(ArticleImage.article))
        .order_by(ArticleImage.created_at.desc())
    )
    matched_files.extend(
        build_article_image_search_read(record)
        for record in article_image_result.scalars().all()
    )

    matched_folders.sort(key=lambda item: item.path.lower())
    matched_files.sort(key=lambda item: item.created_at, reverse=True)
    return FileSearchRead(folders=matched_folders, files=matched_files)


def collect_descendant_folder_ids(folder_map: dict[UUID, FileFolder], folder_ids: set[UUID]) -> set[UUID]:
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


def build_archive_root_name_map(selected_folders: list[FileFolder]) -> dict[UUID, str]:
    """为选中文件夹分配压缩包根目录名。"""
    used_names: set[str] = set()
    root_name_map: dict[UUID, str] = {}
    for folder in selected_folders:
        root_name_map[folder.id] = ensure_unique_archive_path(used_names, folder.name.strip() or 默认普通文件名)
    return root_name_map


def build_regular_file_archive_parts(
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
        lineage = build_folder_lineage(folder_map, folder_map[record.folder_id])
        root_folder = next((item for item in lineage if item.id in archive_root_name_map), None)
        if root_folder is None:
            return []
        return [
            archive_root_name_map[root_folder.id],
            *[item.name for item in lineage if item.id != root_folder.id],
        ]
    if record.folder_id is None:
        return []
    lineage = build_folder_lineage(folder_map, folder_map[record.folder_id])
    return [item.name for item in lineage]


def build_article_image_archive_parts(record: ArticleImage) -> list[str]:
    """构造文章图片在压缩包中的路径前缀。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return [文章图片目录名称, article_title.strip() or "未命名文章"]


async def build_archive_payload(
    db: AsyncSession,
    user: User,
    *,
    folder_ids: list[UUID],
    file_ids: list[UUID],
) -> bytes:
    """构造打包下载的 ZIP 内容。"""
    folders = await list_user_folders(db, user)
    folder_map = {folder.id: folder for folder in folders}

    selected_folder_ids = set(folder_ids)
    for folder_id in selected_folder_ids:
        if folder_id not in folder_map:
            raise HTTPException(status_code=404, detail="存在无效的文件夹选择")

    selected_files: list[File] = []
    if file_ids:
        file_result = await db.execute(
            select(File).where(
                File.user_id == user.id,
                File.purpose == FilePurpose.file,
                File.id.in_(file_ids),
            )
        )
        selected_files = list(file_result.scalars().all())
    selected_article_images: list[ArticleImage] = []
    if file_ids:
        article_image_result = await db.execute(
            select(ArticleImage)
            .join(Article, ArticleImage.article_id == Article.id)
            .where(Article.author_id == user.id, ArticleImage.id.in_(file_ids))
            .options(selectinload(ArticleImage.article))
        )
        selected_article_images = list(article_image_result.scalars().all())
    if len(selected_files) + len(selected_article_images) != len(set(file_ids)):
        raise HTTPException(status_code=404, detail="存在无效的文件选择")

    descendant_folder_ids = collect_descendant_folder_ids(folder_map, selected_folder_ids)
    folder_file_records: list[File] = []
    if descendant_folder_ids:
        folder_file_result = await db.execute(
            select(File).where(
                File.user_id == user.id,
                File.purpose == FilePurpose.file,
                File.folder_id.in_(descendant_folder_ids),
            )
        )
        folder_file_records = list(folder_file_result.scalars().all())

    if not selected_folder_ids and not file_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个文件或文件夹")

    selected_root_folders = [folder_map[folder_id] for folder_id in folder_ids if folder_id in folder_map]
    archive_root_name_map = build_archive_root_name_map(selected_root_folders)
    archive_entries = [
        ArchiveEntry(
            id=record.id,
            original_name=record.original_name,
            storage_key=record.storage_key,
            archive_parts=build_regular_file_archive_parts(
                record,
                descendant_folder_ids=descendant_folder_ids,
                archive_root_name_map=archive_root_name_map,
                folder_map=folder_map,
            ),
        )
        for record in [*selected_files, *folder_file_records]
    ]
    archive_entries.extend(
        ArchiveEntry(
            id=record.id,
            original_name=record.original_name,
            storage_key=record.storage_key,
            archive_parts=build_article_image_archive_parts(record),
        )
        for record in selected_article_images
    )

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
            lineage = build_folder_lineage(folder_map, folder)
            root_folder = next((item for item in lineage if item.id in archive_root_name_map), None)
            if root_folder is None:
                continue
            relative_parts = [item.name for item in lineage if item.id != root_folder.id]
            archive_folder_path = build_archive_file_path([archive_root_name_map[root_folder.id], *relative_parts], "")
            if archive_folder_path and archive_folder_path not in used_archive_folder_paths:
                used_archive_folder_paths.add(archive_folder_path)
                archive.writestr(f"{archive_folder_path}/", b"")

        for entry in archive_entries:
            for index in range(1, len(entry.archive_parts) + 1):
                archive_folder_path = build_archive_file_path(entry.archive_parts[:index], "")
                if archive_folder_path and archive_folder_path not in used_archive_folder_paths:
                    used_archive_folder_paths.add(archive_folder_path)
                    archive.writestr(f"{archive_folder_path}/", b"")

        for entry in archive_entries:
            archive_path = ensure_unique_archive_path(
                used_archive_paths,
                build_archive_file_path(entry.archive_parts, entry.original_name),
            )
            content, _ = fetch_object_bytes(entry.storage_key)
            archive.writestr(archive_path, content)

    return output.getvalue()


async def create_folder(
    db: AsyncSession,
    user: User,
    *,
    name: str,
    parent_id: UUID | None,
) -> FileFolder:
    """创建文件夹。"""
    if parent_id is not None:
        await get_folder_or_404(db, user, parent_id)
    await ensure_unique_folder_name(db, user, name=name, parent_id=parent_id)

    folder = FileFolder(user_id=user.id, parent_id=parent_id, name=name)
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


async def rename_folder(
    db: AsyncSession,
    user: User,
    *,
    folder_id: UUID,
    name: str,
) -> FileFolder:
    """重命名文件夹。"""
    folder = await get_folder_or_404(db, user, folder_id)
    await ensure_unique_folder_name(db, user, name=name, parent_id=folder.parent_id, exclude_folder_id=folder.id)
    folder.name = name
    await db.commit()
    await db.refresh(folder)
    return folder


async def move_folder(
    db: AsyncSession,
    user: User,
    *,
    folder_id: UUID,
    parent_id: UUID | None,
) -> FileFolder:
    """移动文件夹。"""
    folder = await get_folder_or_404(db, user, folder_id)
    await ensure_folder_move_allowed(db, user, folder=folder, parent_id=parent_id)
    await ensure_unique_folder_name(db, user, name=folder.name, parent_id=parent_id, exclude_folder_id=folder.id)
    folder.parent_id = parent_id
    await db.commit()
    await db.refresh(folder)
    return folder


async def delete_folder(
    db: AsyncSession,
    user: User,
    *,
    folder_id: UUID,
) -> None:
    """删除空文件夹。"""
    folder = await get_folder_or_404(db, user, folder_id)

    child_folder_result = await db.execute(
        select(FileFolder.id).where(FileFolder.user_id == user.id, FileFolder.parent_id == folder.id).limit(1)
    )
    if child_folder_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="文件夹下仍有子文件夹，无法删除")

    child_file_result = await db.execute(
        select(File.id)
        .where(File.user_id == user.id, File.purpose == FilePurpose.file, File.folder_id == folder.id)
        .limit(1)
    )
    if child_file_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="文件夹下仍有文件，无法删除")

    await db.delete(folder)
    await db.commit()


async def upload_file_for_purpose(
    db: AsyncSession,
    user: User,
    file: UploadFile,
    *,
    purpose: FilePurpose,
    folder_id: UUID | None = None,
) -> FileRead:
    """按指定用途上传文件并持久化元数据。"""
    content = await file.read()
    if len(content) > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    if purpose is not FilePurpose.file and folder_id is not None:
        raise HTTPException(status_code=400, detail="当前文件类型不支持自定义目录")
    if folder_id is not None:
        await get_folder_or_404(db, user, folder_id)

    original_filename = file.filename or ""
    original_content_type = file.content_type or ""
    validate_upload_purpose(original_filename, original_content_type, purpose)

    prepared_upload = prepare_upload_payload(
        filename=original_filename,
        content_type=original_content_type,
        content=content,
        compress_static_images=should_compress_static_images(purpose),
    )
    storage_key = build_storage_key(
        user.id,
        prepared_upload.storage_name,
        directory=resolve_storage_directory(purpose),
    )
    upload_bytes(
        storage_key=storage_key,
        content=prepared_upload.content,
        content_type=prepared_upload.content_type,
    )

    record = File(
        user_id=user.id,
        folder_id=folder_id,
        purpose=purpose,
        original_name=prepared_upload.original_name,
        storage_key=storage_key,
        size=len(prepared_upload.content),
        mime_type=prepared_upload.content_type,
    )
    db.add(record)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        remove_object_best_effort(storage_key)
        raise

    await db.refresh(record)
    return build_file_read(record)


async def upload_file(
    db: AsyncSession,
    user: User,
    file: UploadFile,
    *,
    folder_id: UUID | None = None,
) -> FileRead:
    """上传普通文件并持久化元数据。"""
    return await upload_file_for_purpose(db, user, file, purpose=FilePurpose.file, folder_id=folder_id)


async def upload_article_image(db: AsyncSession, user: User, file: UploadFile) -> FileRead:
    """上传文章图片并在需要时压缩静态位图。"""
    return await upload_file_for_purpose(db, user, file, purpose=FilePurpose.article_image)


async def move_file(
    db: AsyncSession,
    user: User,
    *,
    file_id: UUID,
    folder_id: UUID | None,
) -> FileRead:
    """移动普通文件。"""
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == user.id, File.purpose == FilePurpose.file)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    if folder_id is not None:
        await get_folder_or_404(db, user, folder_id)

    record.folder_id = folder_id
    await db.commit()
    await db.refresh(record)
    return build_file_read(record)


async def rename_file(
    db: AsyncSession,
    user: User,
    *,
    file_id: UUID,
    original_name: str,
) -> FileRead:
    """重命名普通文件或文章图片。"""
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == user.id, File.purpose == FilePurpose.file)
    )
    record = result.scalar_one_or_none()
    if record is not None:
        record.original_name = normalize_filename_for_content_type(original_name, record.mime_type)
        await db.commit()
        await db.refresh(record)
        return build_file_read(record)

    article_image_result = await db.execute(
        select(ArticleImage)
        .join(Article, ArticleImage.article_id == Article.id)
        .where(ArticleImage.id == file_id, Article.author_id == user.id)
        .options(selectinload(ArticleImage.article))
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    article_title = article_image.article.title if article_image.article is not None else "未命名文章"
    article_image.original_name = normalize_filename_for_content_type(original_name, article_image.mime_type)
    await db.commit()
    await db.refresh(article_image)
    return FileRead(
        id=article_image.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=article_image.original_name,
        url=build_public_url(article_image.storage_key),
        size=article_image.size,
        mime_type=article_image.mime_type,
        created_at=article_image.created_at,
        article_id=article_image.article_id,
        article_title=article_title,
    )


async def delete_file(db: AsyncSession, user: User, file_id: UUID) -> None:
    """删除文件记录，并在提交后清理对象存储。"""
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == user.id, File.purpose == FilePurpose.file)
    )
    record = result.scalar_one_or_none()
    if record is not None:
        storage_key = record.storage_key
        await db.delete(record)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        remove_object_best_effort(storage_key)
        return

    article_image_result = await db.execute(
        select(ArticleImage)
        .join(Article, ArticleImage.article_id == Article.id)
        .where(ArticleImage.id == file_id, Article.author_id == user.id)
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    storage_key = article_image.storage_key
    await db.delete(article_image)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    remove_object_best_effort(storage_key)
