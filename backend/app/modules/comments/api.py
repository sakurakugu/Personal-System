"""带嵌套回复和审核的评论路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.comments.schemas import CommentCreate, CommentLikeRead, CommentModerate, CommentPendingRead, CommentRead
from app.modules.comments.service import (
    comments_enabled,
    create_comment as create_comment_service,
    delete_comment as delete_comment_service,
    ensure_comment_view_permission,
    get_like_status as get_like_status_service,
    like_comment as like_comment_service,
    list_comments as list_comments_service,
    list_pending_comments as list_pending_comments_service,
    moderate_comment as moderate_comment_service,
    unlike_comment as unlike_comment_service,
)
from app.shared.auth.deps import get_current_user, get_current_user_optional, require_admin
from app.shared.db.session import get_db

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("", response_model=list[CommentRead])
async def list_comments(
    article_id: str = Query(...),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取文章的已批准评论及嵌套回复。"""
    if not await comments_enabled(db):
        return []

    await ensure_comment_view_permission(db, current_user)
    return await list_comments_service(db, article_id, current_user)


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """发表评论。"""
    return await create_comment_service(db, body, current_user)


@router.patch("/{comment_id}/moderate", response_model=CommentRead)
async def moderate_comment(
    comment_id: str,
    body: CommentModerate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """审核评论。"""
    return await moderate_comment_service(db, comment_id, body)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除评论。"""
    await delete_comment_service(db, comment_id, user)


@router.get("/pending", response_model=list[CommentPendingRead])
async def list_pending_comments(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取待审核评论列表。"""
    return await list_pending_comments_service(db)


@router.post("/{comment_id}/like", response_model=CommentLikeRead)
async def like_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """点赞评论。"""
    return await like_comment_service(db, comment_id, user)


@router.delete("/{comment_id}/like", response_model=CommentLikeRead)
async def unlike_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消点赞评论。"""
    return await unlike_comment_service(db, comment_id, user)


@router.get("/{comment_id}/like/status", response_model=CommentLikeRead)
async def get_like_status(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户对评论的点赞状态。"""
    return await get_like_status_service(db, comment_id, user)
