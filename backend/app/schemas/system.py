"""系统与统计 Schema。"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """用户仪表板统计数据响应。"""

    total_articles: int
    total_comments: int
    total_views: int
    total_todos: int
    current_month_bill_income_cent: int = 0
    current_month_bill_expense_cent: int = 0
    current_month_bill_net_cent: int = 0
    current_month_bill_record_count: int = 0
    recent_views: list[dict] = []


class TodoCompletionHistoryItemRead(BaseModel):
    """待办完成历史明细项。"""

    todo_id: UUID
    title: str
    completed_count: int


class TodoCompletionHistoryDayRead(BaseModel):
    """待办完成历史单日汇总。"""

    date: date
    completed_count: int
    items: list[TodoCompletionHistoryItemRead] = []


class TodoCompletionHistoryRead(BaseModel):
    """待办完成历史区间响应。"""

    start_date: date
    end_date: date
    max_completed_count: int
    total_completed_count: int
    days: list[TodoCompletionHistoryDayRead]


class SystemStatus(BaseModel):
    """系统状态响应。"""

    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    uptime_seconds: float


class HealthComponentStatus(BaseModel):
    """健康检查组件状态。"""

    status: str
    detail: str | None = None


class HealthCheckRead(BaseModel):
    """健康检查响应。"""

    status: str
    checked_at: datetime
    database: HealthComponentStatus
    redis: HealthComponentStatus


class SystemSettingsRead(BaseModel):
    """系统设置数据响应。"""

    comments_enabled: bool
    comments_stealth: bool
    comments_min_role: str = "guest"
    register_enabled: bool = True


class SystemSettingsUpdate(BaseModel):
    """系统设置更新请求。"""

    comments_enabled: bool | None = None
    comments_stealth: bool | None = None
    comments_min_role: str | None = None
    register_enabled: bool | None = None


class PageViewRecordRequest(BaseModel):
    """页面访问记录请求。"""

    path: str = Field(default="/", max_length=500)
    article_id: UUID | None = None
