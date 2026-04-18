"""文件资源管理路由。"""

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.modules.files.explorer import (
    get_explorer_data as get_explorer_data_service,
    search_resources as search_resources_service,
)
from app.modules.files.operations import (
    build_archive_payload as build_archive_payload_service,
    create_folder as create_folder_service,
    delete_file as delete_file_service,
    delete_folder as delete_folder_service,
    move_file as move_file_service,
    move_folder as move_folder_service,
    rename_file as rename_file_service,
    rename_folder as rename_folder_service,
    upload_file as upload_file_service,
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

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/explorer", response_model=FileExplorerRead)
async def get_explorer_data(
    folder_id: UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取资源管理器目录树与当前目录内容。"""
    return await get_explorer_data_service(db, user, folder_id=folder_id)


@router.get("/search", response_model=FileSearchRead)
async def search_resources(
    keyword: str = Query(min_length=1, max_length=120),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按关键词跨目录搜索资源。"""
    return await search_resources_service(db, user, keyword=keyword)


@router.post("/archive/download")
async def download_archive(
    body: FileArchiveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将选中资源打包为 ZIP 并下载。"""
    archive_bytes = await build_archive_payload_service(
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
async def upload_file(
    file: UploadFile,
    folder_id: UUID | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传普通文件到指定目录。"""
    return await upload_file_service(db, user, file, folder_id=folder_id)


@router.post("/folders", response_model=FileFolderRead, status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FileFolderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建文件夹。"""
    return await create_folder_service(db, user, name=body.name, parent_id=body.parent_id)


@router.patch("/folders/{folder_id}/rename", response_model=FileFolderRead)
async def rename_folder(
    folder_id: UUID,
    body: FileFolderRename,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重命名文件夹。"""
    return await rename_folder_service(db, user, folder_id=folder_id, name=body.name)


@router.patch("/folders/{folder_id}/move", response_model=FileFolderRead)
async def move_folder(
    folder_id: UUID,
    body: FileFolderMove,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """移动文件夹。"""
    return await move_folder_service(db, user, folder_id=folder_id, parent_id=body.parent_id)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除空文件夹。"""
    await delete_folder_service(db, user, folder_id=folder_id)


@router.patch("/{file_id}/move", response_model=FileRead)
async def move_file(
    file_id: UUID,
    body: FileMove,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """移动普通文件。"""
    return await move_file_service(db, user, file_id=file_id, folder_id=body.folder_id)


@router.patch("/{file_id}/rename", response_model=FileRead)
async def rename_file(
    file_id: UUID,
    body: FileRename,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重命名普通文件。"""
    return await rename_file_service(db, user, file_id=file_id, original_name=body.original_name)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除文件。"""
    await delete_file_service(db, user, file_id)
