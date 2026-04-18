"""分类和标签路由。

此模块提供文章分类和标签的管理接口，包括：
- 分类的增删查
- 标签的增删查

所有写入操作需要管理员权限。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import Unix纪元时间, build_conditional_json_response
from app.modules.users.models import User
from app.modules.articles.models import Category, Tag
from app.modules.articles.schemas import CategoryCreate, CategoryRead, TagCreate, TagRead
from app.modules.articles.taxonomy import (
    create_category as create_category_service,
    create_tag as create_tag_service,
    delete_category as delete_category_service,
    delete_tag as delete_tag_service,
    list_categories as list_categories_service,
    list_tags as list_tags_service,
)
from app.shared.auth.deps import require_admin
from app.shared.db.session import get_db

# 创建路由器，标签为 categories & tags
router = APIRouter(tags=["categories & tags"])


# ── 分类 ────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有分类列表（公开接口）。

    按分类名称字母顺序排序。

    Args:
        db: 数据库会话

    Returns:
        list[CategoryRead]: 分类列表
    """
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    payload = await list_categories_service(db)
    last_modified = max((item.created_at for item in categories), default=Unix纪元时间)
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryCreate, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """
    创建新分类（管理员）。

    自动根据名称生成 slug。

    Args:
        body: 分类创建数据
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        CategoryRead: 创建的分类
    """
    return await create_category_service(db, body)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """
    删除分类（管理员）。

    Args:
        category_id: 分类 ID
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 分类不存在
    """
    await delete_category_service(db, category_id)


# ── 标签 ────────────────────────────────────────────────

@router.get("/tags", response_model=list[TagRead])
async def list_tags(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有标签列表（公开接口）。

    按标签名称字母顺序排序。

    Args:
        db: 数据库会话

    Returns:
        list[TagRead]: 标签列表
    """
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    payload = await list_tags_service(db)
    last_modified = max((item.created_at for item in tags), default=Unix纪元时间)
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=300,
    )


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(body: TagCreate, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """
    创建新标签（管理员）。

    自动根据名称生成 slug。

    Args:
        body: 标签创建数据
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        TagRead: 创建的标签
    """
    return await create_tag_service(db, body)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """
    删除标签（管理员）。

    Args:
        tag_id: 标签 ID
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException: 404 - 标签不存在
    """
    await delete_tag_service(db, tag_id)
