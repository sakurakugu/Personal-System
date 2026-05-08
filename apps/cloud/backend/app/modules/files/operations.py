"""文件与文件夹操作。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import User
from app.modules.files.archive import (
    ArchiveEntry,
    构建归档字节,
    构建归档根名称映射,
    构建文章图片归档路径,
    构建动态图片归档路径,
    构建常规文件归档路径,
    收集子孙文件夹ID,
)
from app.modules.files.folders import (
    确保文件夹移动允许,
    确保文件夹名唯一,
    get_folder_or_404,
    列出用户文件夹,
)
from app.modules.files.models import File, FileFolder, FilePurpose
from app.modules.files.presentation import 构建文章图片文件读取, 构建文件读取, 构建动态图片文件读取
from app.modules.files.schemas import FileRead
from app.modules.files.upload_preparation import (
    是否为图片上传,
    按内容类型规范化文件名,
    准备上传载荷,
)
from app.modules.articles.models import Article, ArticleImage
from app.modules.moments.models import Moment, MomentImage
from app.shared.storage.client import (
    构建存储键,
    尽力删除对象,
    upload_bytes,
)

最大上传字节数 = 10 * 1024 * 1024
普通文件存储目录 = "files"
文章图片存储目录 = "articles"


def 解析存储目录(purpose: FilePurpose) -> str:
    """根据文件用途返回对象存储目录。"""
    if purpose is FilePurpose.article_image:
        return 文章图片存储目录
    return 普通文件存储目录


def 是否应压缩静态图片(purpose: FilePurpose) -> bool:
    """根据文件用途判断是否压缩静态位图。"""
    return purpose is FilePurpose.article_image


def 校验上传用途(filename: str, content_type: str, purpose: FilePurpose) -> None:
    """校验上传内容是否符合用途约束。"""
    if purpose is FilePurpose.article_image and not 是否为图片上传(filename, content_type):
        raise HTTPException(status_code=400, detail="文章图片只允许上传图片文件")


async def 构建归档载荷(
    db: AsyncSession,
    user: User,
    *,
    folder_ids: list[UUID],
    file_ids: list[UUID],
) -> bytes:
    """构造打包下载的 ZIP 内容。"""
    folders = await 列出用户文件夹(db, user)
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
            .where(
                Article.author_id == user.id,
                Article.is_deleted.is_(False),
                ArticleImage.id.in_(file_ids),
            )
            .options(selectinload(ArticleImage.article))
        )
        selected_article_images = list(article_image_result.scalars().all())
    selected_moment_images: list[MomentImage] = []
    if file_ids:
        moment_image_result = await db.execute(
            select(MomentImage)
            .join(Moment, MomentImage.moment_id == Moment.id)
            .where(
                Moment.user_id == user.id,
                Moment.is_deleted.is_(False),
                MomentImage.id.in_(file_ids),
            )
            .options(selectinload(MomentImage.moment))
        )
        selected_moment_images = list(moment_image_result.scalars().all())
    if len(selected_files) + len(selected_article_images) + len(selected_moment_images) != len(set(file_ids)):
        raise HTTPException(status_code=404, detail="存在无效的文件选择")

    descendant_folder_ids = 收集子孙文件夹ID(folder_map, selected_folder_ids)
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
    archive_root_name_map = 构建归档根名称映射(selected_root_folders)
    archive_entries = [
        ArchiveEntry(
            id=record.id,
            original_name=record.original_name,
            storage_key=record.storage_key,
            archive_parts=构建常规文件归档路径(
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
            archive_parts=构建文章图片归档路径(record),
        )
        for record in selected_article_images
    )
    archive_entries.extend(
        ArchiveEntry(
            id=record.id,
            original_name=record.original_name,
            storage_key=record.storage_key,
            archive_parts=构建动态图片归档路径(record),
        )
        for record in selected_moment_images
    )

    return 构建归档字节(
        selected_root_folders=selected_root_folders,
        descendant_folder_ids=descendant_folder_ids,
        folder_map=folder_map,
        archive_root_name_map=archive_root_name_map,
        archive_entries=archive_entries,
    )


async def 创建文件夹(
    db: AsyncSession,
    user: User,
    *,
    name: str,
    parent_id: UUID | None,
) -> FileFolder:
    """创建文件夹。"""
    if parent_id is not None:
        await get_folder_or_404(db, user, parent_id)
    await 确保文件夹名唯一(db, user, name=name, parent_id=parent_id)

    folder = FileFolder(user_id=user.id, parent_id=parent_id, name=name)
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


async def 重命名文件夹(
    db: AsyncSession,
    user: User,
    *,
    folder_id: UUID,
    name: str,
) -> FileFolder:
    """重命名文件夹。"""
    folder = await get_folder_or_404(db, user, folder_id)
    await 确保文件夹名唯一(db, user, name=name, parent_id=folder.parent_id, exclude_folder_id=folder.id)
    folder.name = name
    await db.commit()
    await db.refresh(folder)
    return folder


async def 移动文件夹(
    db: AsyncSession,
    user: User,
    *,
    folder_id: UUID,
    parent_id: UUID | None,
) -> FileFolder:
    """移动文件夹。"""
    folder = await get_folder_or_404(db, user, folder_id)
    await 确保文件夹移动允许(db, user, folder=folder, parent_id=parent_id)
    await 确保文件夹名唯一(db, user, name=folder.name, parent_id=parent_id, exclude_folder_id=folder.id)
    folder.parent_id = parent_id
    await db.commit()
    await db.refresh(folder)
    return folder


async def 删除文件夹(
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


async def 按用途上传文件(
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
    校验上传用途(original_filename, original_content_type, purpose)

    prepared_upload = 准备上传载荷(
        filename=original_filename,
        content_type=original_content_type,
        content=content,
        compress_static_images=是否应压缩静态图片(purpose),
    )
    storage_key = 构建存储键(
        user.id,
        prepared_upload.storage_name,
        directory=解析存储目录(purpose),
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
        尽力删除对象(storage_key)
        raise

    await db.refresh(record)
    return 构建文件读取(record)


async def 上传文件(
    db: AsyncSession,
    user: User,
    file: UploadFile,
    *,
    folder_id: UUID | None = None,
) -> FileRead:
    """上传普通文件并持久化元数据。"""
    return await 按用途上传文件(db, user, file, purpose=FilePurpose.file, folder_id=folder_id)


async def 上传文章图片(db: AsyncSession, user: User, file: UploadFile) -> FileRead:
    """上传文章图片并在需要时压缩静态位图。"""
    return await 按用途上传文件(db, user, file, purpose=FilePurpose.article_image)


async def 移动文件(
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
    return 构建文件读取(record)


async def 重命名文件(
    db: AsyncSession,
    user: User,
    *,
    file_id: UUID,
    original_name: str,
) -> FileRead:
    """重命名普通文件、文章图片或动态图片。"""
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == user.id, File.purpose == FilePurpose.file)
    )
    record = result.scalar_one_or_none()
    if record is not None:
        record.original_name = 按内容类型规范化文件名(original_name, record.mime_type)
        await db.commit()
        await db.refresh(record)
        return 构建文件读取(record)

    article_image_result = await db.execute(
        select(ArticleImage)
        .join(Article, ArticleImage.article_id == Article.id)
        .where(
            ArticleImage.id == file_id,
            Article.author_id == user.id,
            Article.is_deleted.is_(False),
        )
        .options(selectinload(ArticleImage.article))
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is not None:
        article_image.original_name = 按内容类型规范化文件名(original_name, article_image.mime_type)
        await db.commit()
        await db.refresh(article_image)
        return 构建文章图片文件读取(article_image)

    moment_image_result = await db.execute(
        select(MomentImage)
        .join(Moment, MomentImage.moment_id == Moment.id)
        .where(
            MomentImage.id == file_id,
            Moment.user_id == user.id,
            Moment.is_deleted.is_(False),
        )
        .options(selectinload(MomentImage.moment))
    )
    moment_image = moment_image_result.scalar_one_or_none()
    if moment_image is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    moment_image.original_name = 按内容类型规范化文件名(original_name, moment_image.mime_type)
    await db.commit()
    await db.refresh(moment_image)
    return 构建动态图片文件读取(moment_image)


async def 删除文件(db: AsyncSession, user: User, file_id: UUID) -> None:
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

        尽力删除对象(storage_key)
        return

    article_image_result = await db.execute(
        select(ArticleImage)
        .join(Article, ArticleImage.article_id == Article.id)
        .where(
            ArticleImage.id == file_id,
            Article.author_id == user.id,
            Article.is_deleted.is_(False),
        )
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is not None:
        storage_key = article_image.storage_key
        await db.delete(article_image)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        尽力删除对象(storage_key)
        return

    moment_image_result = await db.execute(
        select(MomentImage)
        .join(Moment, MomentImage.moment_id == Moment.id)
        .where(
            MomentImage.id == file_id,
            Moment.user_id == user.id,
            Moment.is_deleted.is_(False),
        )
    )
    moment_image = moment_image_result.scalar_one_or_none()
    if moment_image is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    storage_key = moment_image.storage_key
    await db.delete(moment_image)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    尽力删除对象(storage_key)
