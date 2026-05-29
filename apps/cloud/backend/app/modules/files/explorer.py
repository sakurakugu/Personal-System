"""资源管理器查询。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import 用户
from app.modules.files.folders import (
    构建文件夹面包屑,
    构建文件夹完整路径,
    构建文件夹树节点,
    文件范围查询,
    列出用户文件夹,
)
from app.modules.files.models import File, FilePurpose
from app.modules.files.presentation import (
    构建文章图片文件读取,
    构建文章图片搜索读取,
    构建文件读取,
    构建动态图片文件读取,
    构建动态图片搜索读取,
    构建搜索文件读取,
    构建文娱资源文件读取,
    构建文娱资源搜索读取,
    排序资源管理器文件,
)
from app.modules.files.schemas import FileExplorerRead, FileFolderRead, FileFolderSearchRead, FileSearchRead
from app.modules.articles.models import 文章, 文章图片
from app.modules.media.models import 文娱条目, 文娱资源
from app.modules.moments.models import 动态, 动态图片


async def 获取资源管理器数据(
    db: AsyncSession,
    user: 用户,
    *,
    folder_id: UUID | None,
) -> FileExplorerRead:
    """读取资源管理器所需的目录树与当前目录内容。"""
    folders = await 列出用户文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}
    current_folder = folder_map.get(folder_id) if folder_id is not None else None
    if folder_id is not None and current_folder is None:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    child_folders = [folder for folder in folders if folder.parent_id == folder_id]
    file_result = await db.execute(
        文件范围查询(
            select(File)
            .where(File.user_id == user.id, File.purpose == FilePurpose.file)
            .order_by(func.lower(File.original_name), File.created_at.desc()),
            folder_id,
        )
    )
    file_records = list(file_result.scalars().all())
    explorer_files = [构建文件读取(record) for record in file_records]
    if folder_id is None:
        article_image_result = await db.execute(
            select(文章图片)
            .join(文章, 文章图片.article_id == 文章.id)
            .where(文章.author_id == user.id, 文章.is_deleted.is_(False))
            .options(selectinload(文章图片.article))
            .order_by(func.lower(文章图片.original_name), 文章图片.created_at.desc())
        )
        article_image_records = list(article_image_result.scalars().all())
        explorer_files.extend(构建文章图片文件读取(record) for record in article_image_records)
        moment_image_result = await db.execute(
            select(动态图片)
            .join(动态, 动态图片.moment_id == 动态.id)
            .where(动态.user_id == user.id, 动态.is_deleted.is_(False))
            .options(selectinload(动态图片.moment))
            .order_by(func.lower(动态图片.original_name), 动态图片.created_at.desc())
        )
        moment_image_records = list(moment_image_result.scalars().all())
        explorer_files.extend(构建动态图片文件读取(record) for record in moment_image_records)
        media_asset_result = await db.execute(
            select(文娱资源)
            .join(文娱条目, 文娱资源.media_item_id == 文娱条目.id)
            .where(文娱资源.user_id == user.id, 文娱条目.is_deleted.is_(False))
            .options(selectinload(文娱资源.media_item))
            .order_by(func.lower(func.coalesce(文娱资源.original_name, 文娱条目.title)), 文娱资源.created_at.desc())
        )
        media_asset_records = list(media_asset_result.scalars().all())
        explorer_files.extend(构建文娱资源文件读取(record) for record in media_asset_records)

    return FileExplorerRead(
        current_folder=FileFolderRead.model_validate(current_folder) if current_folder is not None else None,
        breadcrumbs=构建文件夹面包屑(folder_map, current_folder),
        tree=构建文件夹树节点(folders),
        folders=[FileFolderRead.model_validate(folder) for folder in child_folders],
        files=排序资源管理器文件(explorer_files),
    )


async def 搜索资源(
    db: AsyncSession,
    user: 用户,
    *,
    keyword: str,
) -> FileSearchRead:
    """按关键词跨目录搜索文件夹与文件。"""
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return FileSearchRead(folders=[], files=[])

    folders = await 列出用户文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}

    matched_folders = [
        FileFolderSearchRead(
            id=folder.id,
            parent_id=folder.parent_id,
            name=folder.name,
            path=构建文件夹完整路径(folder_map, folder),
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
        构建搜索文件读取(
            record,
            path=构建文件夹完整路径(folder_map, folder_map.get(record.folder_id) if record.folder_id else None),
        )
        for record in file_records
    ]
    article_image_result = await db.execute(
        select(文章图片)
        .join(文章, 文章图片.article_id == 文章.id)
        .where(
            文章.author_id == user.id,
            文章.is_deleted.is_(False),
            or_(
                func.lower(文章图片.original_name).contains(normalized_keyword),
                func.lower(文章.title).contains(normalized_keyword),
            ),
        )
        .options(selectinload(文章图片.article))
        .order_by(文章图片.created_at.desc())
    )
    matched_files.extend(
        构建文章图片搜索读取(record)
        for record in article_image_result.scalars().all()
    )
    moment_image_result = await db.execute(
        select(动态图片)
        .join(动态, 动态图片.moment_id == 动态.id)
        .where(
            动态.user_id == user.id,
            动态.is_deleted.is_(False),
            or_(
                func.lower(动态图片.original_name).contains(normalized_keyword),
                func.lower(func.coalesce(动态.title, "")).contains(normalized_keyword),
            ),
        )
        .options(selectinload(动态图片.moment))
        .order_by(动态图片.created_at.desc())
    )
    matched_files.extend(
        构建动态图片搜索读取(record)
        for record in moment_image_result.scalars().all()
    )
    media_asset_result = await db.execute(
        select(文娱资源)
        .join(文娱条目, 文娱资源.media_item_id == 文娱条目.id)
        .where(
            文娱资源.user_id == user.id,
            文娱条目.is_deleted.is_(False),
            or_(
                func.lower(func.coalesce(文娱资源.original_name, "")).contains(normalized_keyword),
                func.lower(文娱条目.title).contains(normalized_keyword),
                func.lower(func.coalesce(文娱条目.original_title, "")).contains(normalized_keyword),
            ),
        )
        .options(selectinload(文娱资源.media_item))
        .order_by(文娱资源.created_at.desc())
    )
    matched_files.extend(
        构建文娱资源搜索读取(record)
        for record in media_asset_result.scalars().all()
    )

    matched_folders.sort(key=lambda item: item.path.lower())
    matched_files.sort(key=lambda item: item.created_at, reverse=True)
    return FileSearchRead(folders=matched_folders, files=matched_files)
