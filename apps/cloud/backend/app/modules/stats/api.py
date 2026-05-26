"""统计和分析路由。"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.stats.schemas import 博客统计, 仪表盘统计, 页面浏览记录请求, 待办完成历史信息
from app.modules.stats.service import 获取博客统计, 获取仪表盘统计, 获取待办完成历史, 记录页面浏览
from app.shared.auth.deps import 获取当前用户, 获取当前用户可选
from app.shared.db.session import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/blog", response_model=博客统计)
async def blog_stats(
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    获取博客公开站点统计。

    Args:
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        博客统计: 博客站点统计
    """
    return await 获取博客统计(db, user=user)


@router.get("/dashboard", response_model=仪表盘统计)
async def dashboard_stats(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户仪表板统计数据。

    Args:
        user: 当前登录用户
        db: 数据库会话

    Returns:
        仪表盘统计: 仪表板统计
    """
    return await 获取仪表盘统计(db, user)


@router.get("/todos/completion-history", response_model=待办完成历史信息)
async def todo_completion_history(
    start_date: date = Query(..., description="开始日期，格式 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期，格式 YYYY-MM-DD"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    获取待办完成历史。

    Args:
        start_date: 开始日期
        end_date: 结束日期
        user: 当前登录用户
        db: 数据库会话

    Returns:
        待办完成历史信息: 完成历史
    """
    return await 获取待办完成历史(
        db,
        user=user,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/pageview", status_code=status.HTTP_204_NO_CONTENT)
async def post_pageview(
    body: 页面浏览记录请求,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    记录页面浏览量。

    Args:
        body: 页面访问请求体
        request: FastAPI 请求对象
        db: 数据库会话
    """
    await 记录页面浏览(
        db,
        body=body,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
