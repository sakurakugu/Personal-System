"""动态（Moments）路由。

此模块提供动态（类似朋友圈/微博短内容）管理接口，包括：
- 登录可见接口：获取已发布的动态列表
- 用户接口：草稿管理、发布动态、删除动态

每个用户只有一个草稿，发布后会自动删除草稿。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.moments.schemas import (
    动态创建,
    动态草稿保存,
    动态草稿信息,
    动态图片排序更新,
    动态图片信息,
    动态点赞信息,
    动态公开信息,
    动态信息,
    动态更新,
    动态浏览信息,
)
from app.modules.moments.image import (
    删除动态图片 as 删除动态图片_service,
    列出动态图片 as 列出动态图片_service,
    重排动态图片 as 重排动态图片_service,
    上传动态图片 as 上传动态图片_service,
)
from app.modules.moments.service import (
    构建动态公开读取,
    删除动态 as 删除动态_service,
    获取草稿 as 获取草稿_service,
    获取公开动态或404,
    点赞动态 as 点赞动态_service,
    列出动态 as 列出动态_service,
    列出我的动态 as 列出我的动态_service,
    发布动态 as 发布动态_service,
    记录动态浏览 as 记录动态浏览_service,
    恢复动态 as 恢复动态_service,
    保存草稿 as 保存草稿_service,
    取消点赞动态 as 取消点赞动态_service,
    更新动态 as 更新动态_service,
)
from app.shared.engagement import 获取访客ID
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db
from fastapi import File, UploadFile

router = APIRouter(prefix="/moments", tags=["moments"])

@router.get("", response_model=PaginatedResponse)
async def 列出动态(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _user: 用户 = Depends(获取当前用户),
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
    return await 列出动态_service(
        db,
        page=page,
        page_size=page_size,
        visitor_id=获取访客ID(request),
    )


@router.get("/public/{moment_id}", response_model=动态公开信息)
async def 获取公开动态(
    moment_id: str,
    request: Request,
    _user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    获取单个已发布动态详情（登录后可见）。

    Args:
        moment_id: 动态 ID
        db: 数据库会话

    Returns:
        动态公开信息: 动态详情

    Raises:
        HTTPException: 404 - 动态不存在
    """
    moment = await 获取公开动态或404(db, moment_id)
    return await 构建动态公开读取(moment, visitor_id=获取访客ID(request))


@router.post("/{moment_id}/like", response_model=动态点赞信息)
async def 点赞动态(
    moment_id: str,
    request: Request,
    response: Response,
    _user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    点赞动态。

    Args:
        moment_id: 动态 ID
        request: 当前请求
        response: 当前响应
        db: 数据库会话

    Returns:
        动态点赞信息: 点赞结果
    """
    return await 点赞动态_service(db, moment_id, request, response)


@router.delete("/{moment_id}/like", response_model=动态点赞信息)
async def 取消点赞动态(
    moment_id: str,
    request: Request,
    _user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    取消点赞动态。

    Args:
        moment_id: 动态 ID
        request: 当前请求
        db: 数据库会话

    Returns:
        动态点赞信息: 取消点赞结果
    """
    return await 取消点赞动态_service(db, moment_id, request)


@router.post("/{moment_id}/view", response_model=动态浏览信息)
async def 记录动态浏览(
    moment_id: str,
    request: Request,
    response: Response,
    _user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    记录动态浏览量。

    Args:
        moment_id: 动态 ID
        request: 当前请求
        response: 当前响应
        db: 数据库会话

    Returns:
        动态浏览信息: 浏览记录结果
    """
    return await 记录动态浏览_service(db, moment_id, request, response)

@router.get("/draft", response_model=动态草稿信息 | None)
async def 获取草稿(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的草稿（只有一个）。

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        动态草稿信息 | None: 草稿或 None
    """
    return await 获取草稿_service(db, user)


@router.put("/draft", response_model=动态草稿信息)
async def 保存草稿(
    body: 动态草稿保存,
    user: 用户 = Depends(获取当前用户),
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
        动态草稿信息: 保存的草稿
    """
    return await 保存草稿_service(db, body, user)


@router.post("/publish", response_model=动态信息, status_code=status.HTTP_201_CREATED)
async def 发布动态(
    body: 动态创建,
    user: 用户 = Depends(获取当前用户),
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
        动态信息: 发布的动态
    """
    return await 发布动态_service(db, body, user)


@router.put("/{moment_id}", response_model=动态信息)
async def 更新动态(
    moment_id: str,
    body: 动态更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新已发布动态。"""
    return await 更新动态_service(db, moment_id, body, user)


@router.get("/{moment_id}/images", response_model=list[动态图片信息])
async def 列出动态图片(
    moment_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取动态图片列表。"""
    return await 列出动态图片_service(db, user, moment_id)


@router.post("/{moment_id}/images", response_model=动态图片信息, status_code=status.HTTP_201_CREATED)
async def 上传动态图片(
    moment_id: str,
    file: UploadFile = File(...),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """上传动态图片。"""
    return await 上传动态图片_service(db, user, moment_id, file)


@router.patch("/{moment_id}/images/order", response_model=list[动态图片信息])
async def 重排动态图片(
    moment_id: str,
    body: 动态图片排序更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新动态图片顺序。"""
    return await 重排动态图片_service(db, user, moment_id, body)


@router.delete("/{moment_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除动态图片(
    moment_id: str,
    image_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除动态图片。"""
    await 删除动态图片_service(db, user, moment_id, image_id)


@router.get("/my/list", response_model=PaginatedResponse)
async def 列出我的动态(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    is_deleted: bool = Query(False, description="是否显示回收站动态"),
    user: 用户 = Depends(获取当前用户),
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
    return await 列出我的动态_service(
        db,
        page=page,
        page_size=page_size,
        user=user,
        is_deleted=is_deleted,
    )


@router.delete("/{moment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除动态(
    moment_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: 用户 = Depends(获取当前用户),
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
    await 删除动态_service(db, moment_id, user, permanent=permanent)


@router.post("/{moment_id}/restore", response_model=动态信息)
async def 恢复动态(
    moment_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    从回收站恢复动态。

    Args:
        moment_id: 动态 ID
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        动态信息: 恢复后的动态
    """
    return await 恢复动态_service(db, moment_id, user)
