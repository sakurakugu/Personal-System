"""评论领域服务。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import get_current_user
from app.models.article import Article, ArticleStatus
from app.models.comment import (
    Comment,
    CommentLike,
    CommentStatus,
)
from app.models.system import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_MIN_ROLE,
    SystemSetting,
)
from app.models.user import User, UserRole
from app.schemas.comment import (
    CommentCreate,
    CommentLikeRead,
    CommentModerate,
    CommentPendingRead,
    CommentRead,
    CommentReplyToUser,
)
from app.schemas.user import UserRead
from app.services.article_service import can_user_read_article

角色等级 = {"guest": 0, "user": 1, "admin": 2, "super_admin": 3}


def _build_user_read(user: User) -> UserRead:
    """构造用户响应，避免 UUIDv7 直接传入 Pydantic。"""
    return UserRead(
        id=UUID(str(user.id)),
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        role=user.role.value,
        avatar_url=user.avatar_url,
        bio=user.bio,
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def comments_enabled(db: AsyncSession) -> bool:
    """检查评论功能是否开启。"""
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_ENABLED)
    return True if setting is None else (setting.bool_value or False)


async def get_comments_min_role(db: AsyncSession) -> str:
    """获取评论最低可见角色。"""
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_MIN_ROLE)
    if setting is None or setting.str_value is None:
        return "guest"
    return setting.str_value


async def resolve_comment_user(
    creds: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    """根据凭证解析当前用户，失败时按游客处理。"""
    if creds is None:
        return None
    try:
        return await get_current_user(creds=creds, db=db)
    except HTTPException:
        return None


async def ensure_comment_view_permission(
    db: AsyncSession,
    current_user: User | None,
) -> None:
    """校验当前用户是否有权查看评论。"""
    min_role = await get_comments_min_role(db)
    min_level = 角色等级.get(min_role, 0)
    if min_level == 0:
        return
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能查看评论",
        )

    user_level = 角色等级.get(current_user.role.value, 0)
    if user_level < min_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法查看评论",
        )


def _comment_detail_query():
    """构建评论详情查询。"""
    return select(Comment).options(
        selectinload(Comment.user),
        selectinload(Comment.parent).selectinload(Comment.user),
    )


async def _get_liked_comment_ids(
    db: AsyncSession,
    comments: list[Comment],
    current_user: User | None,
) -> set[UUID]:
    """查询当前用户对评论集合的点赞状态。"""
    if current_user is None or not comments:
        return set()

    comment_ids = [comment.id for comment in comments]
    result = await db.execute(
        select(CommentLike.comment_id).where(
            CommentLike.comment_id.in_(comment_ids),
            CommentLike.user_id == current_user.id,
        )
    )
    return set(result.scalars().all())


async def _ensure_article_commentable(
    db: AsyncSession,
    article_id: str | UUID,
    current_user: User | None,
) -> Article:
    """校验文章存在且当前用户可访问。"""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    if not can_user_read_article(article, current_user):
        if article.status == ArticleStatus.login_required:
            raise HTTPException(status_code=401, detail="该文章需要登录后查看")
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


def _build_reply_to_user(comment: Comment) -> CommentReplyToUser | None:
    """构造回复目标用户信息。"""
    if comment.parent is None or comment.parent_id is None:
        return None

    parent_user = comment.parent.user
    if parent_user is not None:
        return CommentReplyToUser(
            id=UUID(str(parent_user.id)),
            username=parent_user.username,
            nickname=parent_user.nickname,
            guest_name=comment.parent.guest_name,
        )

    return CommentReplyToUser(
        id=UUID(str(comment.parent_id)),
        username="",
        nickname=None,
        guest_name=comment.parent.guest_name or "匿名",
    )


def _serialize_comment_tree(
    comment: Comment,
    children_map: dict[UUID, list[Comment]],
    liked_comment_ids: set[UUID],
) -> CommentRead:
    """将 ORM 评论树序列化为响应模型。"""
    return CommentRead(
        id=UUID(str(comment.id)),
        article_id=UUID(str(comment.article_id)),
        user_id=UUID(str(comment.user_id)) if comment.user_id is not None else None,
        guest_name=comment.guest_name,
        parent_id=UUID(str(comment.parent_id)) if comment.parent_id is not None else None,
        content=comment.content,
        status=comment.status.value,
        like_count=comment.like_count,
        is_liked=comment.id in liked_comment_ids,
        created_at=comment.created_at,
        user=_build_user_read(comment.user) if comment.user is not None else None,
        reply_to_user=_build_reply_to_user(comment),
        replies=[
            _serialize_comment_tree(child, children_map, liked_comment_ids)
            for child in children_map.get(comment.id, [])
        ],
    )


def build_comment_tree(comments: list[Comment], liked_comment_ids: set[UUID]) -> list[CommentRead]:
    """从扁平评论列表构造嵌套响应树。"""
    children_map: dict[UUID, list[Comment]] = {}
    roots: list[Comment] = []

    for comment in comments:
        if comment.parent_id is None:
            roots.append(comment)
            continue
        children_map.setdefault(comment.parent_id, []).append(comment)

    return [
        _serialize_comment_tree(comment, children_map, liked_comment_ids)
        for comment in roots
    ]


async def list_comments(
    db: AsyncSession,
    article_id: str,
    current_user: User | None,
) -> list[CommentRead]:
    """获取文章评论树。"""
    await _ensure_article_commentable(db, article_id, current_user)
    result = await db.execute(
        _comment_detail_query()
        .where(
            Comment.article_id == article_id,
            Comment.status == CommentStatus.approved,
        )
        .order_by(Comment.created_at.asc())
    )
    comments = list(result.scalars().unique().all())
    liked_comment_ids = await _get_liked_comment_ids(db, comments, current_user)
    return build_comment_tree(comments, liked_comment_ids)


async def _get_comment_or_404(db: AsyncSession, comment_id: str) -> Comment:
    """按 ID 获取评论。"""
    result = await db.execute(_comment_detail_query().where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    return comment


async def _get_comment_read(
    db: AsyncSession,
    comment_id: str,
    current_user: User | None,
) -> CommentRead:
    """按 ID 读取单条评论响应。"""
    comment = await _get_comment_or_404(db, comment_id)
    liked_comment_ids = await _get_liked_comment_ids(db, [comment], current_user)
    return _serialize_comment_tree(comment, {}, liked_comment_ids)


async def create_comment(
    db: AsyncSession,
    body: CommentCreate,
    current_user: User | None,
) -> CommentRead:
    """创建评论。"""
    if not await comments_enabled(db):
        raise HTTPException(status_code=403, detail="评论功能已关闭")
    await _ensure_article_commentable(db, body.article_id, current_user)
    if current_user is None and not body.guest_name:
        raise HTTPException(status_code=400, detail="游客评论需要提供名称")

    comment = Comment(
        article_id=body.article_id,
        user_id=current_user.id if current_user else None,
        guest_name=None if current_user else body.guest_name,
        parent_id=body.parent_id,
        content=body.content,
        status=CommentStatus.approved if current_user else CommentStatus.pending,
    )
    db.add(comment)
    await db.flush()
    return await _get_comment_read(db, str(comment.id), current_user)


async def moderate_comment(db: AsyncSession, comment_id: str, body: CommentModerate) -> CommentRead:
    """审核评论。"""
    comment = await _get_comment_or_404(db, comment_id)
    comment.status = CommentStatus(body.status)
    await db.flush()
    return await _get_comment_read(db, comment_id, None)


async def delete_comment(db: AsyncSession, comment_id: str, user: User) -> None:
    """删除评论。"""
    comment = await _get_comment_or_404(db, comment_id)
    if comment.user_id != user.id and user.role not in (UserRole.admin, UserRole.super_admin):
        raise HTTPException(status_code=403, detail="无权操作")
    await db.delete(comment)


async def list_pending_comments(db: AsyncSession) -> list[CommentPendingRead]:
    """获取待审核评论列表。"""
    result = await db.execute(
        select(Comment)
        .where(Comment.status == CommentStatus.pending)
        .options(
            selectinload(Comment.user),
            joinedload(Comment.article).options(
                selectinload(Article.author),
                selectinload(Article.category),
                selectinload(Article.tags),
            ),
        )
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().unique().all()
    return [CommentPendingRead.model_validate(comment) for comment in comments]


async def like_comment(db: AsyncSession, comment_id: str, user: User) -> CommentLikeRead:
    """点赞评论。"""
    comment = await _get_comment_or_404(db, comment_id)
    await _ensure_article_commentable(db, comment.article_id, user)
    result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="已经点赞过该评论")

    db.add(CommentLike(comment_id=comment_id, user_id=user.id))
    comment.like_count += 1
    await db.flush()
    return CommentLikeRead(
        comment_id=comment_id,
        user_id=user.id,
        is_liked=True,
        like_count=comment.like_count,
    )


async def unlike_comment(db: AsyncSession, comment_id: str, user: User) -> CommentLikeRead:
    """取消点赞评论。"""
    comment = await _get_comment_or_404(db, comment_id)
    await _ensure_article_commentable(db, comment.article_id, user)
    result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id,
        )
    )
    like = result.scalar_one_or_none()
    if like is None:
        raise HTTPException(status_code=400, detail="未点赞该评论")

    await db.delete(like)
    comment.like_count = max(0, comment.like_count - 1)
    await db.flush()
    return CommentLikeRead(
        comment_id=comment_id,
        user_id=user.id,
        is_liked=False,
        like_count=comment.like_count,
    )


async def get_like_status(db: AsyncSession, comment_id: str, user: User) -> CommentLikeRead:
    """获取当前用户的点赞状态。"""
    comment = await _get_comment_or_404(db, comment_id)
    await _ensure_article_commentable(db, comment.article_id, user)
    result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id,
        )
    )
    return CommentLikeRead(
        comment_id=comment_id,
        user_id=user.id,
        is_liked=result.scalar_one_or_none() is not None,
        like_count=comment.like_count,
    )
