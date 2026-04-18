"""资源管理器查询。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleImage
from app.models.file import File, FilePurpose
from app.models.user import User
from app.schemas.file import FileExplorerRead, FileFolderRead, FileFolderSearchRead, FileSearchRead
from app.services.files.folders import (
    build_folder_breadcrumbs,
    build_folder_full_path,
    build_folder_tree_nodes,
    file_scope_query,
    list_user_folders,
)
from app.services.files.presentation import (
    build_article_image_file_read,
    build_article_image_search_read,
    build_file_read,
    build_search_file_read,
    sort_explorer_files,
)


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
