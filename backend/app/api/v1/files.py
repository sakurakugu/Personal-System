"""文件管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.file import FileRead
from app.services.file_service import (
    delete_file as delete_file_service,
    list_files as list_files_service,
    upload_file as upload_file_service,
)

# 创建路由器，前缀为 /files，标签为 files
router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件到 MinIO 对象存储。

    文件大小限制为 10MB，上传后保存文件元数据到数据库。

    Args:
        file: 上传的文件
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        FileRead: 文件信息（包括访问 URL）

    Raises:
        HTTPException: 413 - 文件过大（最大 10MB）
    """
    return await upload_file_service(db, user, file)


@router.get("", response_model=list[FileRead])
async def list_files(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    获取当前用户的普通文件列表。

    按创建时间倒序排列。

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        list[FileRead]: 文件列表
    """
    return await list_files_service(db, user)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除文件。

    从数据库和 MinIO 存储桶中同时删除文件。

    Args:
        file_id: 文件 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 文件不存在
    """
    await delete_file_service(db, user, file_id)
