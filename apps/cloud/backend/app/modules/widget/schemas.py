"""桌面小工具相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WidgetTodoSummaryItemRead(BaseModel):
    """桌面小工具待办摘要项。"""

    id: UUID
    title: str
    is_pinned: bool
    importance: int
    urgency: int
    end_date: datetime | None = None


class WidgetSummaryRead(BaseModel):
    """桌面小工具摘要响应。"""

    user_id: UUID
    username: str
    nickname: str | None = None
    pending_count: int
    pinned_count: int
    overdue_count: int
    due_today_count: int
    items: list[WidgetTodoSummaryItemRead]


class WidgetPublicSummaryRead(BaseModel):
    """桌面小工具公开摘要响应。"""

    pending_count: int
    pinned_count: int
    overdue_count: int
    due_today_count: int
    items: list[WidgetTodoSummaryItemRead]
