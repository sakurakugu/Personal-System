"""友链相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class 友链创建(BaseModel):
    """创建友链请求。"""

    name: str = Field(max_length=100)
    url: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=50)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=100)


class 友链更新(BaseModel):
    """更新友链请求。"""

    name: str | None = Field(default=None, max_length=100)
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=50)
    status: str | None = None


class 友链信息(BaseModel):
    """友链数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    description: str | None = None
    logo_url: str | None = None
    category: str | None = None
    status: str
    is_auto_exchange: bool
    contact_email: str | None = None
    contact_name: str | None = None
    created_at: datetime
    updated_at: datetime


class 友链公开信息(BaseModel):
    """公开可见的友链信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    description: str | None = None
    logo_url: str | None = None
    category: str | None = None


class 友链交换请求(BaseModel):
    """友链交换申请请求。"""

    name: str = Field(max_length=100)
    url: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=50)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=100)
    my_site_url: str = Field(max_length=500)
