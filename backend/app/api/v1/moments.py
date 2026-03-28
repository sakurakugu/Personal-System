"""动态（Moments）路由。

此模块提供动态（类似朋友圈/微博短内容）管理接口，包括：
- 登录可见接口：获取已发布的动态列表
- 用户接口：草稿管理、发布动态、删除动态

每个用户只有一个草稿，发布后会自动删除草稿。
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.moment import Moment
from app.models.user import User
from app.schemas.moment import (
    MomentCreate,
    MomentDraftSave,
    MomentRead,
    MomentPublicRead,
    MomentDraftRead,
)
from app.schemas.shared import (
    PaginatedResponse,
)

# 创建路由器，前缀为 /moments，标签为 moments
router = APIRouter(prefix="/moments", tags=["moments"])


def _moment_query():
    """
    构建动态基础查询，预加载关联数据。

    Returns:
        Select: SQLAlchemy 查询对象，已预加载 user
    """
    return select(Moment).options(selectinload(Moment.user))


# ─────────────────────────────────────────────────────────────
# 首页动态接口（需要登录查看）
# ─────────────────────────────────────────────────────────────

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
    q = _moment_query().where(
        Moment.is_published.is_(True)
    ).order_by(Moment.published_at.desc())

    # 总数
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().unique().all()

    return PaginatedResponse(
        items=[MomentPublicRead.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


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
    result = await db.execute(
        _moment_query().where(
            Moment.id == moment_id,
            Moment.is_published.is_(True)
        )
    )
    moment = result.scalar_one_or_none()
    if not moment:
        raise HTTPException(status_code=404, detail="动态不存在")
    return moment


# ─────────────────────────────────────────────────────────────
# 需要登录的接口
# ─────────────────────────────────────────────────────────────

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
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()
    return draft


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
    # 查找现有草稿
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()

    if draft:
        # 更新现有草稿
        draft.title = body.title
        draft.content = body.content
        draft.updated_at = datetime.now(timezone.utc)
    else:
        # 创建新草稿
        draft = Moment(
            title=body.title,
            content=body.content,
            is_published=False,
            user_id=user.id,
        )
        db.add(draft)

    await db.flush()
    return draft


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
    # 如果有草稿，删除它
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()
    if draft:
        await db.delete(draft)

    # 创建已发布的动态
    now = datetime.now(timezone.utc)
    moment = Moment(
        title=body.title,
        content=body.content,
        is_published=True,
        user_id=user.id,
        published_at=now,
    )
    db.add(moment)
    await db.flush()

    # 重新加载关联数据
    result = await db.execute(_moment_query().where(Moment.id == moment.id))
    return result.scalar_one()


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
    q = (
        _moment_query()
        .where(
            Moment.user_id == user.id,
            Moment.is_published.is_(True)
        )
        .order_by(Moment.published_at.desc())
    )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().unique().all()

    return PaginatedResponse(
        items=[MomentRead.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


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
    result = await db.execute(select(Moment).where(Moment.id == moment_id))
    moment = result.scalar_one_or_none()
    if not moment:
        raise HTTPException(status_code=404, detail="动态不存在")

    # 检查权限
    if moment.user_id != user.id and user.role.value not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="无权操作")

    await db.delete(moment)
