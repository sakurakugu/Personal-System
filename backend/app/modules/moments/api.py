"""动态（Moments）路由。

此模块提供动态（类似朋友圈/微博短内容）管理接口，包括：
- 登录可见接口：获取已发布的动态列表
- 用户接口：草稿管理、发布动态、删除动态

每个用户只有一个草稿，发布后会自动删除草稿。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.moments.schemas import (
    MomentCreate,
    MomentDraftSave,
    MomentDraftRead,
    MomentPublicRead,
    MomentRead,
)
from app.modules.moments.service import (
    delete_moment as delete_moment_service,
    get_draft as get_draft_service,
    get_public_moment_or_404,
    list_moments as list_moments_service,
    list_my_moments as list_my_moments_service,
    publish_moment as publish_moment_service,
    save_draft as save_draft_service,
)
from app.schemas.shared import PaginatedResponse
from app.shared.auth.deps import get_current_user
from app.shared.db.session import get_db

router = APIRouter(prefix="/moments", tags=["moments"])

@router.get("", response_model=PaginatedResponse)
async def list_moments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取已发布的动态列表（登录后可见）。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量，范围 1-50
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的动态列表
    """
    return await list_moments_service(db, page=page, page_size=page_size)


@router.get("/public/{moment_id}", response_model=MomentPublicRead)
async def get_public_moment(
    moment_id: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取单个已发布动态详情（登录后可见）。

    Args:
        moment_id: 动态 ID
        db: 数据库会话

    Returns:
        MomentPublicRead: 动态详情

    Raises:
        HTTPException: 404 - 动态不存在
    """
    return await get_public_moment_or_404(db, moment_id)

@router.get("/draft", response_model=MomentDraftRead | None)
async def get_draft(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的草稿（只有一个）。

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        MomentDraftRead | None: 草稿或 None
    """
    return await get_draft_service(db, user)


@router.put("/draft", response_model=MomentDraftRead)
async def save_draft(
    body: MomentDraftSave,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    保存草稿（每个用户只有一个草稿，自动覆盖）。

    如果已存在草稿则更新，否则创建新草稿。

    Args:
        body: 草稿保存数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        MomentDraftRead: 保存的草稿
    """
    return await save_draft_service(db, body, user)


@router.post("/publish", response_model=MomentRead, status_code=status.HTTP_201_CREATED)
async def publish_moment(
    body: MomentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发布动态。

    如果有草稿，会先删除草稿，然后创建已发布的动态。

    Args:
        body: 动态创建数据
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        MomentRead: 发布的动态
    """
    return await publish_moment_service(db, body, user)


@router.get("/my/list", response_model=PaginatedResponse)
async def list_my_moments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户已发布的动态列表。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量，范围 1-50
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页的动态列表
    """
    return await list_my_moments_service(db, page=page, page_size=page_size, user=user)


@router.delete("/{moment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_moment(
    moment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除动态。

    只能删除自己的动态，管理员可以删除任何人的动态。

    Args:
        moment_id: 动态 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 动态不存在
        HTTPException: 403 - 无权操作
    """
    await delete_moment_service(db, moment_id, user)
