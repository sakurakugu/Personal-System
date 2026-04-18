"""系统 Schema 兼容入口。"""

from app.modules.system.schemas import (
    BlogStats,
    DashboardStats,
    HealthCheckRead,
    HealthComponentStatus,
    PageViewRecordRequest,
    SystemRequestAggregateRead,
    SystemRequestEventRead,
    SystemRuntimeSnapshotRead,
    SystemSettingsRead,
    SystemSettingsUpdate,
    SystemStatus,
    TodoCompletionHistoryDayRead,
    TodoCompletionHistoryItemRead,
    TodoCompletionHistoryRead,
)

__all__ = [
    "BlogStats",
    "DashboardStats",
    "HealthCheckRead",
    "HealthComponentStatus",
    "PageViewRecordRequest",
    "SystemRequestAggregateRead",
    "SystemRequestEventRead",
    "SystemRuntimeSnapshotRead",
    "SystemSettingsRead",
    "SystemSettingsUpdate",
    "SystemStatus",
    "TodoCompletionHistoryDayRead",
    "TodoCompletionHistoryItemRead",
    "TodoCompletionHistoryRead",
]
