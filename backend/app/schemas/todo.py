"""待办相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TodoCreate(BaseModel):
    """创建待办事项请求。"""

    title: str = Field(max_length=300)
    description: str | None = None
    importance: int = Field(default=33, ge=0, le=100)
    urgency: int = Field(default=33, ge=0, le=100)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_pinned: bool = False
    tags: list[str] | None = None
    recurrence_type: str = "none"
    recurrence_interval: int = Field(default=1, ge=1, le=365)
    recurrence_count: int = Field(default=0, ge=-1, le=999)
    times_per_interval: int = Field(default=1, ge=1, le=999)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | str | None) -> list[str] | None:
        """统一标签格式为去重后的标签数组。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("，", ",").split(",")
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags)) or None

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, value: str) -> str:
        """校验循环类型。"""
        allowed = {"none", "daily", "weekly", "monthly", "yearly", "workday", "weekend", "holiday", "custom"}
        if value not in allowed:
            raise ValueError("循环类型不合法")
        return value

    @model_validator(mode="after")
    def validate_recurrence_fields(self) -> "TodoCreate":
        """校验循环相关字段组合是否合法。"""
        if self.recurrence_type == "none":
            if self.recurrence_count != 0:
                raise ValueError("不循环任务的循环次数必须为 0")
            if self.times_per_interval != 1:
                raise ValueError("不循环任务的每周期完成次数必须为 1")
        return self


class TodoUpdate(BaseModel):
    """更新待办事项请求。"""

    title: str | None = None
    description: str | None = None
    status: str | None = None
    importance: int | None = Field(default=None, ge=0, le=100)
    urgency: int | None = Field(default=None, ge=0, le=100)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_pinned: bool | None = None
    is_deleted: bool | None = None
    tags: list[str] | None = None
    recurrence_type: str | None = None
    recurrence_interval: int | None = Field(default=None, ge=1, le=365)
    recurrence_count: int | None = Field(default=None, ge=-1, le=999)
    times_per_interval: int | None = Field(default=None, ge=1, le=999)
    interval_progress: int | None = Field(default=None, ge=0, le=999)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | str | None) -> list[str] | None:
        """统一标签格式为去重后的标签数组。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("，", ",").split(",")
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags)) or None

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, value: str | None) -> str | None:
        """校验循环类型。"""
        if value is None:
            return None
        allowed = {"none", "daily", "weekly", "monthly", "yearly", "workday", "weekend", "holiday", "custom"}
        if value not in allowed:
            raise ValueError("循环类型不合法")
        return value

    @model_validator(mode="after")
    def validate_progress_fields(self) -> "TodoUpdate":
        """校验更新时的循环进度字段。"""
        if self.interval_progress is not None and self.times_per_interval is not None:
            if self.interval_progress > self.times_per_interval:
                raise ValueError("当前周期进度不能大于每周期完成次数")
        if self.recurrence_type == "none":
            if self.recurrence_count not in (None, 0):
                raise ValueError("不循环任务的循环次数必须为 0")
            if self.times_per_interval not in (None, 1):
                raise ValueError("不循环任务的每周期完成次数必须为 1")
        return self


class TodoRead(BaseModel):
    """待办事项数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    status: str
    importance: int
    urgency: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_pinned: bool
    is_deleted: bool
    deleted_at: datetime | None = None
    tags: list[str] | None = None
    recurrence_type: str = "none"
    recurrence_interval: int = 1
    recurrence_count: int = 0
    times_per_interval: int = 1
    interval_progress: int = 0
    progress_reset_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TodoTagRead(BaseModel):
    """待办标签响应。"""

    name: str
    count: int
