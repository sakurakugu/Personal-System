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


class BlogStats(BaseModel):
    """博客站点统计响应。"""

    total_articles: int
    total_categories: int
    total_tags: int
    total_words: int
    last_published_at: datetime | None = None


class TodoCompletionHistoryItemRead(BaseModel):
    """待办完成历史明细项。"""

    todo_id: UUID
    title: str
    completed_count: int
    normalized_score: float


class TodoCompletionHistoryDayRead(BaseModel):
    """待办完成历史单日汇总。"""

    date: date
    completed_count: int
    score: float
    items: list[TodoCompletionHistoryItemRead] = []


class TodoCompletionHistoryRead(BaseModel):
    """待办完成历史区间响应。"""

    start_date: date
    end_date: date
    max_completed_count: int
    total_completed_count: int
    max_score: float
    total_score: float
    days: list[TodoCompletionHistoryDayRead]


class SystemRequestEventRead(BaseModel):
    """系统请求事件。"""

    method: str
    path: str
    status_code: int
    duration_ms: float
    happened_at: datetime
    detail: str | None = None


class SystemRequestAggregateRead(BaseModel):
    """系统请求聚合项。"""

    method: str
    path: str
    count: int
    last_status_code: int
    last_happened_at: datetime
    max_duration_ms: float
    avg_duration_ms: float
    detail: str | None = None


class SystemRuntimeSnapshotRead(BaseModel):
    """系统运行摘要。"""

    recent_window_minutes: int
    slow_request_threshold_ms: float
    error_count: int = 0
    slow_request_count: int = 0
    top_error_routes: list[SystemRequestAggregateRead] = []
    top_slow_routes: list[SystemRequestAggregateRead] = []
    recent_errors: list[SystemRequestEventRead] = []
    recent_slow_requests: list[SystemRequestEventRead] = []


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
    health: "HealthCheckRead"
    runtime: SystemRuntimeSnapshotRead


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
    minio: HealthComponentStatus


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
