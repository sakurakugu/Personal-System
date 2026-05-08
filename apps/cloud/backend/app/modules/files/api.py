"""文件资源管理路由。"""

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.modules.users.models import User
from app.modules.files.explorer import (
    获取资源管理器数据 as 获取资源管理器数据_service,
    搜索资源 as 搜索资源_service,
)
from app.modules.files.operations import (
    构建归档载荷 as 构建归档载荷_service,
    创建文件夹 as 创建文件夹_service,
    删除文件 as 删除文件_service,
    删除文件夹 as 删除文件夹_service,
    移动文件 as 移动文件_service,
    移动文件夹 as 移动文件夹_service,
    重命名文件 as 重命名文件_service,
    重命名文件夹 as 重命名文件夹_service,
    上传文件 as 上传文件_service,
)
from app.modules.files.schemas import (
    FileArchiveRequest,
    FileExplorerRead,
    FileFolderCreate,
    FileFolderMove,
    FileFolderRead,
    FileFolderRename,
    FileMove,
    FileRename,
    FileRead,
    FileSearchRead,
)
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/explorer", response_model=FileExplorerRead)
async def 获取资源管理器数据(
    folder_id: UUID | None = Query(default=None),
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取资源管理器目录树与当前目录内容。"""
    return await 获取资源管理器数据_service(db, user, folder_id=folder_id)


@router.get("/search", response_model=FileSearchRead)
async def 搜索资源(
    keyword: str = Query(min_length=1, max_length=120),
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """按关键词跨目录搜索资源。"""
    return await 搜索资源_service(db, user, keyword=keyword)


@router.post("/archive/download")
async def 下载归档(
    body: FileArchiveRequest,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将选中资源打包为 ZIP 并下载。"""
    archive_bytes = await 构建归档载荷_service(
        db,
        user,
        folder_ids=body.folder_ids,
        file_ids=body.file_ids,
    )
    archive_name = body.archive_name or "resources"
    filename = f"{archive_name}.zip"
    quoted_filename = quote(filename)
    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted_filename}"},
    )


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def 上传文件(
    file: UploadFile,
    folder_id: UUID | None = Form(default=None),
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """上传普通文件到指定目录。"""
    return await 上传文件_service(db, user, file, folder_id=folder_id)


@router.post("/folders", response_model=FileFolderRead, status_code=status.HTTP_201_CREATED)
async def 创建文件夹(
    body: FileFolderCreate,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建文件夹。"""
    return await 创建文件夹_service(db, user, name=body.name, parent_id=body.parent_id)


@router.patch("/folders/{folder_id}/rename", response_model=FileFolderRead)
async def 重命名文件夹(
    folder_id: UUID,
    body: FileFolderRename,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """重命名文件夹。"""
    return await 重命名文件夹_service(db, user, folder_id=folder_id, name=body.name)


@router.patch("/folders/{folder_id}/move", response_model=FileFolderRead)
async def 移动文件夹(
    folder_id: UUID,
    body: FileFolderMove,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """移动文件夹。"""
    return await 移动文件夹_service(db, user, folder_id=folder_id, parent_id=body.parent_id)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除文件夹(
    folder_id: UUID,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除空文件夹。"""
    await 删除文件夹_service(db, user, folder_id=folder_id)


@router.patch("/{file_id}/move", response_model=FileRead)
async def 移动文件(
    file_id: UUID,
    body: FileMove,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """移动普通文件。"""
    return await 移动文件_service(db, user, file_id=file_id, folder_id=body.folder_id)


@router.patch("/{file_id}/rename", response_model=FileRead)
async def 重命名文件(
    file_id: UUID,
    body: FileRename,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """重命名普通文件。"""
    return await 重命名文件_service(db, user, file_id=file_id, original_name=body.original_name)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除文件(
    file_id: UUID,
    user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除文件。"""
    await 删除文件_service(db, user, file_id)
