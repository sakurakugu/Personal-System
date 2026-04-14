"""分类和标签路由。

此模块提供文章分类和标签的管理接口，包括：
- 分类的增删查
- 标签的增删查

所有写入操作需要管理员权限。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from slugify import slugify
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import Unix纪元时间, build_conditional_json_response
from app.core.database import get_db
from app.api.deps import require_admin
from app.models.article import Article, Category, Tag
from app.models.user import User
from app.schemas.article import CategoryCreate, CategoryRead, TagCreate, TagRead

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
    payload = [CategoryRead.model_validate(item) for item in categories]
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
    cat = Category(name=body.name, slug=slugify(body.name), description=body.description)
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return cat


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
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    await db.execute(
        update(Article)
        .where(Article.category_id == category_id)
        .values(category_id=None)
    )
    await db.delete(cat)


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
    payload = [TagRead.model_validate(item) for item in tags]
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
    tag = Tag(name=body.name, slug=slugify(body.name))
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


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
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    await db.delete(tag)
