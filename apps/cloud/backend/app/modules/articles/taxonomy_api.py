"""分类和标签路由。

此模块提供文章分类和标签的管理接口，包括：
- 分类的增删查
- 标签的增删查

所有写入操作需要管理员权限。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.http_cache import 构建条件JSON响应
from app.modules.users.models import 用户
from app.modules.articles.schemas import 分类创建, 分类信息, 标签创建, 标签信息
from app.modules.articles.taxonomy import (
    创建分类 as 创建分类_service,
    创建标签 as 创建标签_service,
    删除分类 as 删除分类_service,
    删除标签 as 删除标签_service,
    列出分类 as 列出分类_service,
    列出标签 as 列出标签_service,
    列出可见分类 as 列出可见分类_service,
    列出可见标签 as 列出可见标签_service,
)
from app.shared.auth.deps import 获取当前用户, 获取当前用户可选, 要求管理员权限
from app.shared.db.session import get_db

# 创建路由器，标签为 categories & tags
router = APIRouter(tags=["categories & tags"])


# ── 分类 ────────────────────────────────────────────────

@router.get("/categories", response_model=list[分类信息])
async def 列出分类(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前访问者可见文章使用的分类列表（公开接口）。

    按分类名称字母顺序排序。

    Args:
        db: 数据库会话

    Returns:
        list[分类信息]: 分类列表
    """
    payload, last_modified = await 列出可见分类_service(db, user)
    return 构建条件JSON响应(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="private" if user is not None else "public",
        max_age=300,
    )


@router.get("/categories/all", response_model=list[分类信息])
async def 列出全部分类(_user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """获取全部分类列表（后台编辑使用）。"""
    return await 列出分类_service(db)


@router.post("/categories", response_model=分类信息, status_code=status.HTTP_201_CREATED)
async def 创建分类(body: 分类创建, _admin: 用户 = Depends(要求管理员权限), db: AsyncSession = Depends(get_db)):
    """
    创建新分类（管理员）。

    自动根据名称生成 slug。

    Args:
        body: 分类创建数据
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        分类信息: 创建的分类
    """
    return await 创建分类_service(db, body)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除分类(category_id: str, _admin: 用户 = Depends(要求管理员权限), db: AsyncSession = Depends(get_db)):
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
    await 删除分类_service(db, category_id)


# ── 标签 ────────────────────────────────────────────────

@router.get("/tags", response_model=list[标签信息])
async def 列出标签(
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前访问者可见文章使用的标签列表（公开接口）。

    按标签名称字母顺序排序。

    Args:
        db: 数据库会话

    Returns:
        list[标签信息]: 标签列表
    """
    payload, last_modified = await 列出可见标签_service(db, user)
    return 构建条件JSON响应(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="private" if user is not None else "public",
        max_age=300,
    )


@router.get("/tags/all", response_model=list[标签信息])
async def 列出全部标签(_user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """获取全部标签列表（后台编辑使用）。"""
    return await 列出标签_service(db)


@router.post("/tags", response_model=标签信息, status_code=status.HTTP_201_CREATED)
async def 创建标签(body: 标签创建, _admin: 用户 = Depends(要求管理员权限), db: AsyncSession = Depends(get_db)):
    """
    创建新标签（管理员）。

    自动根据名称生成 slug。

    Args:
        body: 标签创建数据
        _admin: 当前管理员用户（依赖注入）
        db: 数据库会话

    Returns:
        标签信息: 创建的标签
    """
    return await 创建标签_service(db, body)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除标签(tag_id: str, _admin: 用户 = Depends(要求管理员权限), db: AsyncSession = Depends(get_db)):
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
    await 删除标签_service(db, tag_id)
