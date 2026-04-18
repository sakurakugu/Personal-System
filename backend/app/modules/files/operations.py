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
    build_archive_bytes,
    build_archive_root_name_map,
    build_article_image_archive_parts,
    build_regular_file_archive_parts,
    collect_descendant_folder_ids,
)
from app.modules.files.folders import (
    ensure_folder_move_allowed,
    ensure_unique_folder_name,
    get_folder_or_404,
    list_user_folders,
)
from app.modules.files.models import File, FileFolder, FilePurpose
from app.modules.files.presentation import build_article_image_file_read, build_file_read
from app.modules.files.schemas import FileRead
from app.modules.files.upload_preparation import (
    is_image_upload,
    normalize_filename_for_content_type,
    prepare_upload_payload,
)
from app.modules.articles.models import Article, ArticleImage
from app.services.storage_service import (
    build_storage_key,
    remove_object_best_effort,
    upload_bytes,
)

最大上传字节数 = 10 * 1024 * 1024
普通文件存储目录 = "files"
文章图片存储目录 = "articles"


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

    return build_archive_bytes(
        selected_root_folders=selected_root_folders,
        descendant_folder_ids=descendant_folder_ids,
        folder_map=folder_map,
        archive_root_name_map=archive_root_name_map,
        archive_entries=archive_entries,
    )


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

    article_image.original_name = normalize_filename_for_content_type(original_name, article_image.mime_type)
    await db.commit()
    await db.refresh(article_image)
    return build_article_image_file_read(article_image)


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
