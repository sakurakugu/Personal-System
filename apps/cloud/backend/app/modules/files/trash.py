"""文件回收站服务。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.files.archive import 收集子孙文件夹ID
from app.modules.files.folders import 构建文件夹完整路径
from app.modules.files.models import File, FileFolder, FilePurpose
from app.modules.files.schemas import FileTrashItemRead, FileTrashRead
from app.shared.db.session import async_session_factory
from app.shared.storage.client import 尽力删除多个对象

logger = logging.getLogger(__name__)

回收站保留天数 = 30
自动清理间隔秒数 = 24 * 60 * 60
_自动清理任务: asyncio.Task[None] | None = None


def 当前UTC时间() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def 计算清理时间(now: datetime) -> datetime:
    """计算回收站资源可自动清理时间。"""
    return now + timedelta(days=回收站保留天数)


def 计算剩余天数(purge_after: datetime, now: datetime) -> int:
    """计算距离自动清理还剩多少天。"""
    seconds = max(0.0, (purge_after - now).total_seconds())
    return max(0, int((seconds + 86_399) // 86_400))


def 应用文件删除状态(record: File, *, user_id: UUID, now: datetime) -> None:
    """将普通文件移入回收站。"""
    record.is_deleted = True
    record.deleted_at = now
    record.deleted_by = user_id
    record.purge_after = 计算清理时间(now)
    record.purged_at = None


def 应用文件夹删除状态(folder: FileFolder, *, user_id: UUID, now: datetime) -> None:
    """将普通文件夹移入回收站。"""
    folder.is_deleted = True
    folder.deleted_at = now
    folder.deleted_by = user_id
    folder.purge_after = 计算清理时间(now)


def 恢复文件删除状态(record: File) -> None:
    """恢复普通文件删除状态。"""
    record.is_deleted = False
    record.deleted_at = None
    record.deleted_by = None
    record.purge_after = None
    record.purged_at = None


def 恢复文件夹删除状态(folder: FileFolder) -> None:
    """恢复普通文件夹删除状态。"""
    folder.is_deleted = False
    folder.deleted_at = None
    folder.deleted_by = None
    folder.purge_after = None


async def _读取用户全部文件夹(db: AsyncSession, user: 用户) -> list[FileFolder]:
    """读取用户全部文件夹，包含回收站资源。"""
    result = await db.execute(
        select(FileFolder)
        .where(FileFolder.user_id == user.id)
        .order_by(FileFolder.parent_id.asc().nullsfirst(), FileFolder.created_at.asc())
    )
    return list(result.scalars().all())


def _收集文件夹子树(folder_map: dict[UUID, FileFolder], folder_id: UUID) -> list[FileFolder]:
    """收集文件夹自身和全部子文件夹。"""
    descendants = 收集子孙文件夹ID(folder_map, {folder_id})
    return [folder for folder_id in descendants if (folder := folder_map.get(folder_id)) is not None]


async def _读取文件夹子树普通文件(db: AsyncSession, user: 用户, folder_ids: set[UUID]) -> list[File]:
    """读取目录子树下的普通文件。"""
    if not folder_ids:
        return []
    result = await db.execute(
        select(File).where(
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.folder_id.in_(folder_ids),
        )
    )
    return list(result.scalars().all())


async def 移入回收站文件(db: AsyncSession, user: 用户, file_id: UUID) -> None:
    """将普通文件移入回收站。"""
    await 移入回收站文件记录(db, user, file_id, commit=True)


async def 移入回收站文件记录(db: AsyncSession, user: 用户, file_id: UUID, *, commit: bool) -> File:
    """将普通文件移入回收站并返回记录。"""
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(False),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    now = 当前UTC时间()
    应用文件删除状态(record, user_id=user.id, now=now)
    if commit:
        await db.commit()
    logger.info("文件已移入回收站：user_id=%s file_id=%s purge_after=%s", user.id, file_id, record.purge_after)
    return record


async def 移入回收站文件夹(db: AsyncSession, user: 用户, folder_id: UUID) -> None:
    """将普通文件夹子树移入回收站。"""
    await 移入回收站文件夹子树(db, user, folder_id, commit=True)


async def 移入回收站文件夹子树(db: AsyncSession, user: 用户, folder_id: UUID, *, commit: bool) -> list[FileFolder]:
    """将普通文件夹子树移入回收站并返回文件夹子树。"""
    folders = await _读取用户全部文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}
    target = folder_map.get(folder_id)
    if target is None or target.is_deleted:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    subtree = _收集文件夹子树(folder_map, folder_id)
    subtree_ids = {folder.id for folder in subtree}
    files = await _读取文件夹子树普通文件(db, user, subtree_ids)
    now = 当前UTC时间()
    for folder in subtree:
        应用文件夹删除状态(folder, user_id=user.id, now=now)
    for record in files:
        应用文件删除状态(record, user_id=user.id, now=now)

    if commit:
        await db.commit()
    logger.info(
        "文件夹已移入回收站：user_id=%s folder_id=%s folders=%s files=%s",
        user.id,
        folder_id,
        len(subtree),
        len(files),
    )
    return subtree


def _构建回收站文件夹路径(folder_map: dict[UUID, FileFolder], folder: FileFolder) -> str:
    """构造回收站文件夹原路径。"""
    visible_map = {folder_id: item for folder_id, item in folder_map.items() if not item.is_deleted or item.id == folder.id}
    return 构建文件夹完整路径(visible_map, folder)


def _构建回收站文件路径(folder_map: dict[UUID, FileFolder], record: File) -> str:
    """构造回收站文件原路径。"""
    folder = folder_map.get(record.folder_id) if record.folder_id else None
    return 构建文件夹完整路径(folder_map, folder)


async def 列出回收站资源(db: AsyncSession, user: 用户) -> FileTrashRead:
    """列出当前用户回收站顶层资源。"""
    now = 当前UTC时间()
    folders = await _读取用户全部文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}
    deleted_folders = [folder for folder in folders if folder.is_deleted]
    top_deleted_folders = [
        folder
        for folder in deleted_folders
        if folder.parent_id is None or not (parent := folder_map.get(folder.parent_id)) or not parent.is_deleted
    ]

    file_result = await db.execute(
        select(File).where(
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(True),
        )
    )
    deleted_files = list(file_result.scalars().all())
    top_deleted_files = [
        record
        for record in deleted_files
        if record.folder_id is None or not (parent := folder_map.get(record.folder_id)) or not parent.is_deleted
    ]

    items: list[FileTrashItemRead] = []
    for folder in top_deleted_folders:
        if folder.deleted_at is None or folder.purge_after is None:
            continue
        items.append(
            FileTrashItemRead(
                id=folder.id,
                type="folder",
                name=folder.name,
                original_parent_id=folder.parent_id,
                path=_构建回收站文件夹路径(folder_map, folder),
                deleted_at=folder.deleted_at,
                purge_after=folder.purge_after,
                remaining_days=计算剩余天数(folder.purge_after, now),
            )
        )

    for record in top_deleted_files:
        if record.deleted_at is None or record.purge_after is None:
            continue
        items.append(
            FileTrashItemRead(
                id=record.id,
                type="file",
                name=record.original_name,
                original_parent_id=record.folder_id,
                path=_构建回收站文件路径(folder_map, record),
                deleted_at=record.deleted_at,
                purge_after=record.purge_after,
                remaining_days=计算剩余天数(record.purge_after, now),
                size=record.size,
                mime_type=record.mime_type,
            )
        )

    items.sort(key=lambda item: item.deleted_at, reverse=True)
    return FileTrashRead(items=items)


def _读取父链(folder_map: dict[UUID, FileFolder], folder_id: UUID | None) -> list[FileFolder]:
    """读取从目标父目录到根目录的父链。"""
    parents: list[FileFolder] = []
    cursor_id = folder_id
    visited: set[UUID] = set()
    while cursor_id is not None and cursor_id not in visited:
        visited.add(cursor_id)
        folder = folder_map.get(cursor_id)
        if folder is None:
            break
        parents.append(folder)
        cursor_id = folder.parent_id
    return parents


async def _确保恢复文件夹名称无冲突(
    db: AsyncSession,
    user: 用户,
    *,
    folder: FileFolder,
    restored_ids: set[UUID],
) -> None:
    """校验恢复文件夹不会与现有同级目录重名。"""
    query = select(FileFolder.id).where(
        FileFolder.user_id == user.id,
        FileFolder.is_deleted.is_(False),
        FileFolder.id.not_in(restored_ids),
        FileFolder.name.ilike(folder.name),
    )
    if folder.parent_id is None:
        query = query.where(FileFolder.parent_id.is_(None))
    else:
        query = query.where(FileFolder.parent_id == folder.parent_id)
    result = await db.execute(query.limit(1))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="同级目录下已存在同名文件夹")


async def 恢复回收站文件(db: AsyncSession, user: 用户, file_id: UUID) -> None:
    """从回收站恢复普通文件。"""
    await 恢复回收站文件记录(db, user, file_id, commit=True)


async def 恢复回收站文件记录(db: AsyncSession, user: 用户, file_id: UUID, *, commit: bool) -> File:
    """从回收站恢复普通文件并返回记录。"""
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(True),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在或未被删除")

    folders = await _读取用户全部文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}
    parents = _读取父链(folder_map, record.folder_id)
    restored_ids = {folder.id for folder in parents}
    for folder in parents:
        if folder.is_deleted:
            await _确保恢复文件夹名称无冲突(db, user, folder=folder, restored_ids=restored_ids)

    for folder in parents:
        恢复文件夹删除状态(folder)
    恢复文件删除状态(record)
    if commit:
        await db.commit()
    logger.info("文件已从回收站恢复：user_id=%s file_id=%s", user.id, file_id)
    return record


async def 恢复回收站文件夹(db: AsyncSession, user: 用户, folder_id: UUID) -> None:
    """从回收站恢复普通文件夹子树。"""
    await 恢复回收站文件夹子树(db, user, folder_id, commit=True)


async def 恢复回收站文件夹子树(db: AsyncSession, user: 用户, folder_id: UUID, *, commit: bool) -> list[FileFolder]:
    """从回收站恢复普通文件夹子树并返回恢复范围。"""
    folders = await _读取用户全部文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}
    target = folder_map.get(folder_id)
    if target is None or not target.is_deleted:
        raise HTTPException(status_code=404, detail="文件夹不存在或未被删除")

    subtree = _收集文件夹子树(folder_map, folder_id)
    parents = _读取父链(folder_map, target.parent_id)
    folders_to_restore = [*parents, *subtree]
    restored_ids = {folder.id for folder in folders_to_restore}
    for folder in folders_to_restore:
        if folder.is_deleted:
            await _确保恢复文件夹名称无冲突(db, user, folder=folder, restored_ids=restored_ids)

    subtree_ids = {folder.id for folder in subtree}
    files = await _读取文件夹子树普通文件(db, user, subtree_ids)
    for folder in folders_to_restore:
        恢复文件夹删除状态(folder)
    for record in files:
        if record.is_deleted:
            恢复文件删除状态(record)

    if commit:
        await db.commit()
    logger.info(
        "文件夹已从回收站恢复：user_id=%s folder_id=%s folders=%s files=%s",
        user.id,
        folder_id,
        len(folders_to_restore),
        len(files),
    )
    return folders_to_restore


async def 彻底删除回收站文件(db: AsyncSession, user: 用户, file_id: UUID) -> None:
    """彻底删除回收站中的普通文件。"""
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(True),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在或未被删除")

    storage_keys = [record.storage_key]
    await db.delete(record)
    await db.commit()
    logger.info("文件已彻底删除：user_id=%s file_id=%s objects=%s", user.id, file_id, len(storage_keys))
    尽力删除多个对象(storage_keys)


async def 彻底删除回收站文件夹(db: AsyncSession, user: 用户, folder_id: UUID) -> None:
    """彻底删除回收站中的普通文件夹子树。"""
    folders = await _读取用户全部文件夹(db, user)
    folder_map = {folder.id: folder for folder in folders}
    target = folder_map.get(folder_id)
    if target is None or not target.is_deleted:
        raise HTTPException(status_code=404, detail="文件夹不存在或未被删除")

    subtree = _收集文件夹子树(folder_map, folder_id)
    subtree_ids = {folder.id for folder in subtree}
    files = await _读取文件夹子树普通文件(db, user, subtree_ids)
    storage_keys = [record.storage_key for record in files]
    for record in files:
        await db.delete(record)
    for folder in subtree:
        await db.delete(folder)
    await db.commit()
    logger.info(
        "文件夹已彻底删除：user_id=%s folder_id=%s folders=%s files=%s objects=%s",
        user.id,
        folder_id,
        len(subtree),
        len(files),
        len(storage_keys),
    )
    尽力删除多个对象(storage_keys)


async def 清理过期回收站文件(db: AsyncSession, *, now: datetime | None = None, limit: int = 500) -> dict[str, int]:
    """清理过期回收站文件和文件夹。"""
    resolved_now = now or 当前UTC时间()
    file_result = await db.execute(
        select(File)
        .where(
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(True),
            File.purge_after <= resolved_now,
        )
        .order_by(File.purge_after.asc())
        .limit(limit)
    )
    expired_files = list(file_result.scalars().all())

    folder_result = await db.execute(
        select(FileFolder)
        .where(
            FileFolder.is_deleted.is_(True),
            FileFolder.purge_after <= resolved_now,
        )
        .order_by(FileFolder.purge_after.asc())
        .limit(limit)
    )
    expired_folders = list(folder_result.scalars().all())

    if not expired_files and not expired_folders:
        return {"users": 0, "files": 0, "folders": 0, "objects": 0}

    all_folder_result = await db.execute(select(FileFolder).where(FileFolder.is_deleted.is_(True)))
    folder_map = {folder.id: folder for folder in all_folder_result.scalars().all()}
    expired_folder_ids: set[UUID] = set()
    for folder in expired_folders:
        expired_folder_ids.update(收集子孙文件夹ID(folder_map, {folder.id}))

    folder_files: list[File] = []
    if expired_folder_ids:
        folder_file_result = await db.execute(
            select(File).where(
                File.purpose == FilePurpose.file,
                File.is_deleted.is_(True),
                File.folder_id.in_(expired_folder_ids),
            )
        )
        folder_files = list(folder_file_result.scalars().all())

    file_map = {record.id: record for record in [*expired_files, *folder_files]}
    storage_keys = [record.storage_key for record in file_map.values()]
    user_ids = {record.user_id for record in file_map.values()}
    expired_folder_records: list[FileFolder] = []
    for folder_id in expired_folder_ids:
        expired_folder = folder_map.get(folder_id)
        if expired_folder is None:
            continue
        user_ids.add(expired_folder.user_id)
        expired_folder_records.append(expired_folder)

    for record in file_map.values():
        await db.delete(record)
    expired_folder_records.sort(key=lambda item: len(_读取父链(folder_map, item.parent_id)), reverse=True)
    for folder in expired_folder_records:
        await db.delete(folder)
    await db.commit()

    logger.info(
        "已清理过期回收站资源：users=%s files=%s folders=%s objects=%s",
        len(user_ids),
        len(file_map),
        len(expired_folder_ids),
        len(storage_keys),
    )
    尽力删除多个对象(storage_keys)
    return {
        "users": len(user_ids),
        "files": len(file_map),
        "folders": len(expired_folder_ids),
        "objects": len(storage_keys),
    }


async def _回收站自动清理循环() -> None:
    """周期清理过期回收站资源。"""
    try:
        while True:
            try:
                async with async_session_factory() as session:
                    await 清理过期回收站文件(session)
            except Exception:
                logger.exception("自动清理过期回收站资源失败")
            await asyncio.sleep(自动清理间隔秒数)
    except asyncio.CancelledError:
        raise


async def 启动文件回收站自动清理() -> None:
    """启动文件回收站自动清理任务。"""
    global _自动清理任务
    if _自动清理任务 is not None and not _自动清理任务.done():
        return
    async with async_session_factory() as session:
        await 清理过期回收站文件(session)
    _自动清理任务 = asyncio.create_task(_回收站自动清理循环())


async def 停止文件回收站自动清理() -> None:
    """停止文件回收站自动清理任务。"""
    global _自动清理任务
    if _自动清理任务 is None:
        return
    task = _自动清理任务
    _自动清理任务 = None
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
