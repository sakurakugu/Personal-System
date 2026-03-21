"""带嵌套回复和审核的评论路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.models import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_MIN_ROLE,
    Comment,
    CommentStatus,
    SystemSetting,
    User,
)
from app.schemas.schemas import CommentCreate, CommentModerate, CommentRead

router = APIRouter(prefix="/comments", tags=["comments"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _comments_enabled(db: AsyncSession) -> bool:
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_ENABLED)
    return True if setting is None else (setting.bool_value or False)


async def _get_comments_min_role(db: AsyncSession) -> str:
    """获取评论最低可见角色设置，默认为 guest"""
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_MIN_ROLE)
    if setting is None or setting.str_value is None:
        return "guest"
    return setting.str_value


async def _check_view_permission(
    min_role: str,
    creds: HTTPAuthorizationCredentials | None,
    db: AsyncSession
) -> User | None:
    """检查用户是否有权限查看评论"""
    role_hierarchy = {"guest": 0, "user": 1, "admin": 2, "super_admin": 3}
    min_level = role_hierarchy.get(min_role, 0)
    
    # guest 级别，任何人都可以看
    if min_level == 0:
        return None
    
    # 其他级别需要登录
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="需要登录才能查看评论"
        )
    
    # 获取当前用户
    from app.api.deps import get_current_user
    try:
        user = await get_current_user(creds=creds, db=db)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="需要登录才能查看评论"
        )
    
    user_level = role_hierarchy.get(user.role.value, 0)
    if user_level < min_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="权限不足，无法查看评论"
        )
    
    return user


@router.get("", response_model=list[CommentRead])
async def list_comments(
    request: Request,
    article_id: str = Query(...),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """获取文章的已批准顶级评论及其嵌套回复。权限由系统设置控制。"""
    if not await _comments_enabled(db):
        return []
    
    # 检查查看权限
    min_role = await _get_comments_min_role(db)
    await _check_view_permission(min_role, creds, db)
    
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
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """发表评论（支持登录用户和游客）"""
    if not await _comments_enabled(db):
        raise HTTPException(status_code=403, detail="评论功能已关闭")
    
    # 获取当前用户（如果已登录）
    user: User | None = None
    if creds:
        try:
            user = await get_current_user(creds=creds, db=db)
        except HTTPException:
            pass  # Token 无效，当作游客处理
    
    # 游客必须提供名称
    if user is None and not body.guest_name:
        raise HTTPException(status_code=400, detail="游客评论需要提供名称")
    
    comment = Comment(
        article_id=body.article_id,
        user_id=user.id if user else None,
        guest_name=None if user else body.guest_name,
        parent_id=body.parent_id,
        content=body.content,
        status=CommentStatus.approved if user else CommentStatus.pending,  # 游客评论需要审核
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
        raise HTTPException(status_code=404, detail="评论不存在")
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
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="无权操作")
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
