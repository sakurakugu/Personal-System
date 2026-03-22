"""带嵌套回复和审核的评论路由。

此模块提供文章评论的管理接口，包括：
- 获取文章的评论列表（支持嵌套回复）
- 发表评论（支持登录用户和游客）
- 评论审核（管理员）
- 删除评论

评论权限由系统设置控制。
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.models import (
    SYSTEM_SETTING_COMMENTS_ENABLED,
    SYSTEM_SETTING_COMMENTS_MIN_ROLE,
    Comment,
    CommentLike,
    CommentStatus,
    SystemSetting,
    User,
)
from app.schemas.schemas import CommentCreate, CommentModerate, CommentRead, CommentPendingRead, CommentLikeRead, CommentReplyToUser

# 创建路由器，前缀为 /comments，标签为 comments
router = APIRouter(prefix="/comments", tags=["comments"])
bearer_scheme = HTTPBearer(auto_error=False)


async def _comments_enabled(db: AsyncSession) -> bool:
    """
    检查评论功能是否开启。

    Args:
        db: 数据库会话

    Returns:
        bool: 评论功能是否开启
    """
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_ENABLED)
    return True if setting is None else (setting.bool_value or False)


async def _get_comments_min_role(db: AsyncSession) -> str:
    """
    获取评论最低可见角色设置。

    Args:
        db: 数据库会话

    Returns:
        str: 最低角色要求，默认为 "guest"
    """
    setting = await db.get(SystemSetting, SYSTEM_SETTING_COMMENTS_MIN_ROLE)
    if setting is None or setting.str_value is None:
        return "guest"
    return setting.str_value


async def _check_view_permission(
    min_role: str,
    creds: HTTPAuthorizationCredentials | None,
    db: AsyncSession
) -> User | None:
    """
    检查用户是否有权限查看评论。

    根据系统设置的最低角色要求检查用户权限。

    Args:
        min_role: 最低角色要求
        creds: HTTP 认证凭证
        db: 数据库会话

    Returns:
        User | None: 当前用户（如果需要登录）或 None

    Raises:
        HTTPException: 401 - 需要登录才能查看评论
        HTTPException: 403 - 权限不足
    """
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
    """
    获取文章的已批准顶级评论及其嵌套回复。

    权限由系统设置控制，支持游客评论和登录用户评论。

    Args:
        request: FastAPI 请求对象
        article_id: 文章 ID（必需）
        creds: HTTP 认证凭证（可选）
        db: 数据库会话

    Returns:
        list[CommentRead]: 评论列表（包含嵌套回复）
    """
    if not await _comments_enabled(db):
        return []

    # 检查查看权限
    min_role = await _get_comments_min_role(db)
    await _check_view_permission(min_role, creds, db)

    # 获取当前用户（如果已登录）
    current_user: User | None = None
    if creds:
        try:
            current_user = await get_current_user(creds=creds, db=db)
        except HTTPException:
            pass

    # 查询所有已批准的评论（包括顶级和回复），并预加载 replies 的 user
    result = await db.execute(
        select(Comment)
        .where(
            Comment.article_id == article_id,
            Comment.status == CommentStatus.approved,
        )
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user),
            selectinload(Comment.parent).selectinload(Comment.user)
        )
        .order_by(Comment.created_at.asc())
    )
    all_comments = result.scalars().unique().all()

    # 如果用户已登录，查询该用户对所有这些评论的点赞状态
    liked_comment_ids: set[UUID] = set()
    if current_user and all_comments:
        comment_ids = [c.id for c in all_comments]
        result = await db.execute(
            select(CommentLike.comment_id).where(
                CommentLike.comment_id.in_(comment_ids),
                CommentLike.user_id == current_user.id
            )
        )
        liked_comment_ids = set(result.scalars().all())  # type: ignore[arg-type]

    # 构建评论树：顶级评论 + 嵌套回复
    top_level: list[Comment] = []
    replies_map: dict[UUID, list[Comment]] = {}

    # 收集所有回复，按 parent_id 分组
    for c in all_comments:
        # 设置点赞状态
        c.__dict__['is_liked'] = c.id in liked_comment_ids
        if c.parent_id is not None:
            if c.parent_id not in replies_map:
                replies_map[c.parent_id] = []
            replies_map[c.parent_id].append(c)

    # 构建顶级评论列表，并附加它们的回复
    for c in all_comments:
        if c.parent_id is None:
            # 直接在 instance 的 __dict__ 中设置，绕过 SQLAlchemy 关系拦截
            c.__dict__['replies'] = replies_map.get(c.id, [])
            top_level.append(c)

    # 为回复评论设置 reply_to_user 信息
    for c in all_comments:
        if c.parent_id is not None and c.parent:
            parent_user = c.parent.user
            if parent_user:
                c.__dict__['reply_to_user'] = CommentReplyToUser(
                    id=parent_user.id,
                    username=parent_user.username,
                    nickname=parent_user.nickname,
                    guest_name=c.parent.guest_name
                )
            else:
                # 父评论是游客评论
                c.__dict__['reply_to_user'] = CommentReplyToUser(
                    id=c.parent_id,
                    username='',
                    nickname=None,
                    guest_name=c.parent.guest_name or '匿名'
                )

    return top_level


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    发表评论（支持登录用户和游客）。

    登录用户评论直接通过审核，游客评论需要管理员审核。

    Args:
        body: 评论创建数据
        creds: HTTP 认证凭证（可选，游客可不提供）
        db: 数据库会话

    Returns:
        CommentRead: 创建的评论

    Raises:
        HTTPException: 403 - 评论功能已关闭
        HTTPException: 400 - 游客评论需要提供名称
    """
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

    # 重新查询以加载关系，用于响应序列化
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment.id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user)
        )
    )
    return result.scalar_one()


@router.patch("/{comment_id}/moderate", response_model=CommentRead)
async def moderate_comment(
    comment_id: str,
    body: CommentModerate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    审核评论（管理员）。

    可以批准或拒绝待审核的评论。

    Args:
        comment_id: 评论 ID
        body: 审核数据（approved 或 rejected）
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        CommentRead: 审核后的评论

    Raises:
        HTTPException: 404 - 评论不存在
    """
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(
            selectinload(Comment.user),
            selectinload(Comment.replies).selectinload(Comment.user)
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    comment.status = CommentStatus(body.status)
    await db.flush()
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除评论。

    用户可以删除自己的评论，管理员可以删除任何评论。

    Args:
        comment_id: 评论 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 评论不存在
        HTTPException: 403 - 无权操作
    """
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="无权操作")
    await db.delete(comment)


@router.get("/pending", response_model=list[CommentPendingRead])
async def list_pending_comments(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取待审核的评论列表（管理员）。

    Args:
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        list[CommentPendingRead]: 待审核评论列表
    """
    result = await db.execute(
        select(Comment)
        .where(Comment.status == CommentStatus.pending)
        .options(
            selectinload(Comment.user),
            joinedload(Comment.article)
        )
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().unique().all()


@router.post("/{comment_id}/like", response_model=CommentLikeRead)
async def like_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    点赞评论（登录用户）。

    Args:
        comment_id: 评论 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        CommentLikeRead: 点赞信息

    Raises:
        HTTPException: 404 - 评论不存在
        HTTPException: 400 - 已经点赞过
    """
    # 检查评论是否存在
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 检查是否已经点赞
    result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已经点赞过该评论")

    # 创建点赞记录
    like = CommentLike(comment_id=comment_id, user_id=user.id)
    db.add(like)

    # 更新点赞计数
    comment.like_count += 1
    await db.flush()

    return {
        "comment_id": comment_id,
        "user_id": user.id,
        "is_liked": True,
        "like_count": comment.like_count
    }


@router.delete("/{comment_id}/like", response_model=CommentLikeRead)
async def unlike_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    取消点赞评论（登录用户）。

    Args:
        comment_id: 评论 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        CommentLikeRead: 点赞信息

    Raises:
        HTTPException: 404 - 评论不存在或未点赞
    """
    # 检查评论是否存在
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 检查是否已点赞
    result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id
        )
    )
    like = result.scalar_one_or_none()
    if not like:
        raise HTTPException(status_code=400, detail="未点赞该评论")

    # 删除点赞记录
    await db.delete(like)

    # 更新点赞计数
    comment.like_count = max(0, comment.like_count - 1)
    await db.flush()

    return {
        "comment_id": comment_id,
        "user_id": user.id,
        "is_liked": False,
        "like_count": comment.like_count
    }


@router.get("/{comment_id}/like/status")
async def get_like_status(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户对评论的点赞状态。

    Args:
        comment_id: 评论 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        dict: 点赞状态和点赞总数
    """
    # 检查评论是否存在
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 检查是否已点赞
    result = await db.execute(
        select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user.id
        )
    )
    is_liked = result.scalar_one_or_none() is not None

    return {
        "comment_id": comment_id,
        "is_liked": is_liked,
        "like_count": comment.like_count
    }
