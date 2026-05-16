"""系统与统计 Schema。"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class 仪表盘统计(BaseModel):
    """用户仪表板统计数据响应。"""

    total_articles: int
    total_views: int
    total_todos: int
    current_month_bill_income_cent: int = 0
    current_month_bill_expense_cent: int = 0
    current_month_bill_net_cent: int = 0
    current_month_bill_record_count: int = 0
    recent_views: list[dict] = []


class 博客统计(BaseModel):
    """博客站点统计响应。"""

    total_articles: int
    total_categories: int
    total_tags: int
    total_words: int
    last_published_at: datetime | None = None


class 待办完成历史项信息(BaseModel):
    """待办完成历史明细项。"""

    todo_id: UUID
    title: str
    completed_count: int
    normalized_score: float


class 待办完成历史日信息(BaseModel):
    """待办完成历史单日汇总。"""

    date: date
    completed_count: int
    score: float
    items: list[待办完成历史项信息] = []


class 待办完成历史信息(BaseModel):
    """待办完成历史区间响应。"""

    start_date: date
    end_date: date
    max_completed_count: int
    total_completed_count: int
    max_score: float
    total_score: float
    days: list[待办完成历史日信息]


class 系统请求事件信息(BaseModel):
    """系统请求事件。"""

    method: str
    path: str
    status_code: int
    duration_ms: float
    happened_at: datetime
    detail: str | None = None


class 系统请求聚合信息(BaseModel):
    """系统请求聚合项。"""

    method: str
    path: str
    count: int
    last_status_code: int
    last_happened_at: datetime
    max_duration_ms: float
    avg_duration_ms: float
    detail: str | None = None


class 系统运行时快照信息(BaseModel):
    """系统运行摘要。"""

    recent_window_minutes: int
    slow_request_threshold_ms: float
    error_count: int = 0
    slow_request_count: int = 0
    top_error_routes: list[系统请求聚合信息] = []
    top_slow_routes: list[系统请求聚合信息] = []
    recent_errors: list[系统请求事件信息] = []
    recent_slow_requests: list[系统请求事件信息] = []


class 系统状态(BaseModel):
    """系统状态响应。"""

    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    uptime_seconds: float
    health: "健康检查信息"
    runtime: 系统运行时快照信息


class 健康组件状态(BaseModel):
    """健康检查组件状态。"""

    status: str
    detail: str | None = None


class 健康检查信息(BaseModel):
    """健康检查响应。"""

    status: str
    checked_at: datetime
    database: 健康组件状态
    redis: 健康组件状态
    minio: 健康组件状态


class 系统设置信息(BaseModel):
    """系统设置数据响应。"""

    register_enabled: bool = False
    comments_enabled: bool = False
    comments_hidden: bool = True


class 系统设置更新(BaseModel):
    """系统设置更新请求。"""

    register_enabled: bool | None = None
    comments_enabled: bool | None = None
    comments_hidden: bool | None = None


class Twikoo密码状态信息(BaseModel):
    """Twikoo 管理密码备忘与运维状态。"""

    available: bool
    detail: str
    last_reset_password: str | None = None
    last_reset_at: datetime | None = None


class Twikoo密码重置请求(BaseModel):
    """Twikoo 管理密码重置请求。"""

    password: str = Field(min_length=6, max_length=128)


class 页面浏览记录请求(BaseModel):
    """页面访问记录请求。"""

    path: str = Field(default="/", max_length=500)
    article_id: UUID | None = None
