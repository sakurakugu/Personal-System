"""文件夹相关辅助。"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.files.models import File, FileFolder
from app.modules.files.schemas import FileBreadcrumbRead, FileFolderTreeNodeRead

根目录名称 = "全部文件"


def 构建文件夹树节点(folders: list[FileFolder]) -> list[FileFolderTreeNodeRead]:
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


def 构建文件夹面包屑(
    folder_map: dict[UUID, FileFolder],
    current_folder: FileFolder | None,
) -> list[FileBreadcrumbRead]:
    """构造当前目录的导航栏。"""
    breadcrumbs = [FileBreadcrumbRead(id=None, name=根目录名称)]
    if current_folder is None:
        return breadcrumbs

    current_path: list[FileBreadcrumbRead] = []
    cursor: FileFolder | None = current_folder
    while cursor is not None:
        current_path.append(FileBreadcrumbRead(id=cursor.id, name=cursor.name))
        cursor = folder_map.get(cursor.parent_id) if cursor.parent_id is not None else None

    breadcrumbs.extend(reversed(current_path))
    return breadcrumbs


def 构建文件夹完整路径(folder_map: dict[UUID, FileFolder], folder: FileFolder | None) -> str:
    """构造文件夹完整路径。"""
    if folder is None:
        return 根目录名称

    parts = [item.name for item in 构建文件夹谱系(folder_map, folder)]
    return " / ".join([根目录名称, *parts])


def 构建文件夹谱系(folder_map: dict[UUID, FileFolder], folder: FileFolder) -> list[FileFolder]:
    """返回从根到当前文件夹的路径。"""
    lineage: list[FileFolder] = []
    cursor: FileFolder | None = folder
    while cursor is not None:
        lineage.append(cursor)
        cursor = folder_map.get(cursor.parent_id) if cursor.parent_id is not None else None
    return list(reversed(lineage))


def 文件夹范围查询(query: Select[tuple[FileFolder]], parent_id: UUID | None) -> Select[tuple[FileFolder]]:
    """为文件夹查询追加父级范围。"""
    if parent_id is None:
        return query.where(FileFolder.parent_id.is_(None))
    return query.where(FileFolder.parent_id == parent_id)


def 文件范围查询(query: Select[tuple[File]], folder_id: UUID | None) -> Select[tuple[File]]:
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


async def 列出用户文件夹(db: AsyncSession, user: User) -> list[FileFolder]:
    """读取当前用户的全部文件夹。"""
    result = await db.execute(
        select(FileFolder)
        .where(FileFolder.user_id == user.id)
        .order_by(FileFolder.parent_id.asc().nullsfirst(), func.lower(FileFolder.name), FileFolder.created_at.asc())
    )
    return list(result.scalars().all())


async def 确保文件夹名唯一(
    db: AsyncSession,
    user: User,
    *,
    name: str,
    parent_id: UUID | None,
    exclude_folder_id: UUID | None = None,
) -> None:
    """校验同级目录下文件夹名称唯一。"""
    query = 文件夹范围查询(
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


async def 确保文件夹移动允许(
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

    folder_map = {item.id: item for item in await 列出用户文件夹(db, user)}
    target_folder = folder_map.get(parent_id)
    if target_folder is None:
        raise HTTPException(status_code=404, detail="目标文件夹不存在")

    cursor: FileFolder | None = target_folder
    while cursor is not None:
        if cursor.id == folder.id:
            raise HTTPException(status_code=400, detail="文件夹不能移动到自己的子目录中")
        cursor = folder_map.get(cursor.parent_id) if cursor.parent_id is not None else None
