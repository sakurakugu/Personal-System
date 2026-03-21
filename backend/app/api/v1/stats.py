"""统计和分析路由。

此模块提供数据统计接口，包括：
- 用户仪表板统计（文章数、评论数、浏览量等）
- 页面浏览量记录
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Article, Comment, PageView, Todo, User
from app.schemas.schemas import DashboardStats

# 创建路由器，前缀为 /stats，标签为 stats
router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户仪表板统计数据。

    统计信息包括：
    - 用户文章总数
    - 用户文章收到的评论总数
    - 用户文章总浏览量
    - 用户待办事项总数
    - 最近 7 天浏览量趋势

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        DashboardStats: 仪表板统计数据
    """
    # 用户文章总数
    total_articles = (await db.execute(
        select(func.count()).where(Article.author_id == user.id)
    )).scalar() or 0

    # 用户文章评论总数
    total_comments = (await db.execute(
        select(func.count()).select_from(Comment).join(Article).where(Article.author_id == user.id)
    )).scalar() or 0

    # 用户文章总浏览量
    total_views = (await db.execute(
        select(func.coalesce(func.sum(Article.view_count), 0)).where(Article.author_id == user.id)
    )).scalar() or 0

    # 待办事项总数
    total_todos = (await db.execute(
        select(func.count()).where(Todo.user_id == user.id)
    )).scalar() or 0

    # 最近 7 天浏览量
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = await db.execute(
        select(
            cast(PageView.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(PageView.created_at >= seven_days_ago)
        .group_by("date")
        .order_by("date")
    )
    recent_views = [{"date": str(row.date), "count": row.count} for row in recent]

    return DashboardStats(
        total_articles=total_articles,
        total_comments=total_comments,
        total_views=total_views,
        total_todos=total_todos,
        recent_views=recent_views,
    )


@router.post("/pageview", status_code=204)
async def record_pageview(request: Request, db: AsyncSession = Depends(get_db)):
    """
    记录页面浏览量（由前端调用）。

    记录页面访问信息，包括访问路径、文章 ID、IP 哈希（隐私保护）和 User-Agent。

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        None
    """
    import hashlib
    body = await request.json()
    path = body.get("path", "/")
    article_id = body.get("article_id")
    ip = request.client.host if request.client else "unknown"
    # 对 IP 进行哈希处理，保护用户隐私
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")[:500]

    pv = PageView(
        path=path,
        article_id=article_id,
        ip_hash=ip_hash,
        user_agent=ua,
    )
    db.add(pv)
