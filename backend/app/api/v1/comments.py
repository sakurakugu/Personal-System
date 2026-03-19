"""带嵌套回复和审核的评论路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional, require_admin
from app.models.models import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    Comment,
    CommentStatus,
    SystemSetting,
    User,
)
from app.schemas.schemas import CommentCreate, CommentModerate, CommentRead

router = APIRouter(prefix="/comments", tags=["comments"])


async def _comments_enabled(db: AsyncSession) -> bool:
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_ENABLED)
    return True if setting is None else setting.bool_value


@router.get("", response_model=list[CommentRead])
async def list_comments(
    article_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """获取文章的已批准顶级评论及其嵌套回复。"""
    if not await _comments_enabled(db):
        return []
    result = await db.execute(
        select(Comment)
        .where(
            Comment.article_id == article_id,
            Comment.parent_id.is_(None),
            Comment.status == CommentStatus.approved,
        )
        .options(selectinload(Comment.user), selectinload(Comment.replies).selectinload(Comment.user))
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().unique().all()


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if not await _comments_enabled(db):
        raise HTTPException(status_code=403, detail="Comments are disabled")
    comment = Comment(
        article_id=body.article_id,
        user_id=user.id if user else None,
        guest_name=body.guest_name if not user else None,
        parent_id=body.parent_id,
        content=body.content,
        status=CommentStatus.approved if user else CommentStatus.pending,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return comment


@router.patch("/{comment_id}/moderate", response_model=CommentRead)
async def moderate_comment(
    comment_id: str,
    body: CommentModerate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.status = CommentStatus(body.status)
    await db.flush()
    await db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.delete(comment)


@router.get("/pending", response_model=list[CommentRead])
async def list_pending_comments(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.status == CommentStatus.pending)
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().all()
