"""统计和分析路由。"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.stats.schemas import BlogStats, DashboardStats, PageViewRecordRequest, TodoCompletionHistoryRead
from app.modules.stats.service import get_blog_stats, get_dashboard_stats, get_todo_completion_history, record_pageview
from app.shared.auth.deps import get_current_user
from app.shared.db.session import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/blog", response_model=BlogStats)
async def blog_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取博客公开站点统计。

    Args:
        db: 数据库会话

    Returns:
        BlogStats: 博客站点统计
    """
    return await get_blog_stats(db)


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户仪表板统计数据。

    Args:
        user: 当前登录用户
        db: 数据库会话

    Returns:
        DashboardStats: 仪表板统计
    """
    return await get_dashboard_stats(db, user)


@router.get("/todos/completion-history", response_model=TodoCompletionHistoryRead)
async def todo_completion_history(
    start_date: date = Query(..., description="开始日期，格式 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期，格式 YYYY-MM-DD"),
    user: User = Depends(get_current_user),
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
        TodoCompletionHistoryRead: 完成历史
    """
    return await get_todo_completion_history(
        db,
        user=user,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/pageview", status_code=status.HTTP_204_NO_CONTENT)
async def post_pageview(
    body: PageViewRecordRequest,
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
    await record_pageview(
        db,
        body=body,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
