"""设备认证相关 Schema。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.auth.device_models import 设备会话范围, 设备会话类型
from app.modules.users.schemas import 用户信息
from app.shared.kernel.validation import 校验用户名


class 设备登录请求(BaseModel):
    """设备登录请求。"""

    username: str
    password: str
    device_name: str = Field(min_length=1, max_length=100)
    device_type: 设备会话类型
    scope: 设备会话范围
    client_version: str | None = Field(default=None, max_length=50)
    platform: str | None = Field(default=None, max_length=50)

    @field_validator("username")
    @classmethod
    def 校验用户名字段(cls, value: str) -> str:
        """规范化用户名。"""
        return 校验用户名(value)

    @field_validator("device_name")
    @classmethod
    def normalize_device_name(cls, value: str) -> str:
        """规范化设备名称。"""
        normalized = value.strip()
        if not normalized:
            raise ValueError("设备名称不能为空")
        return normalized


class 设备开发者登录请求(BaseModel):
    """开发环境设备快捷登录请求。"""

    device_name: str = Field(min_length=1, max_length=100)
    device_type: 设备会话类型
    scope: 设备会话范围
    client_version: str | None = Field(default=None, max_length=50)
    platform: str | None = Field(default=None, max_length=50)

    @field_validator("device_name")
    @classmethod
    def normalize_device_name(cls, value: str) -> str:
        """规范化设备名称。"""
        normalized = value.strip()
        if not normalized:
            raise ValueError("设备名称不能为空")
        return normalized


class 小组件令牌签发请求(BaseModel):
    """小工具凭证签发请求。"""

    device_name: str = Field(min_length=1, max_length=100)
    client_version: str | None = Field(default=None, max_length=50)
    platform: str | None = Field(default=None, max_length=50)

    @field_validator("device_name")
    @classmethod
    def normalize_device_name(cls, value: str) -> str:
        """规范化设备名称。"""
        normalized = value.strip()
        if not normalized:
            raise ValueError("设备名称不能为空")
        return normalized


class 设备会话信息(BaseModel):
    """设备会话响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    device_name: str
    device_type: str
    scope: str
    client_version: str | None = None
    platform: str | None = None
    last_ip: str | None = None
    last_user_agent: str | None = None
    expires_at: datetime
    last_used_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_device_session_source(cls, value: Any) -> Any:
        """兼容从 ORM 对象读取枚举字段。"""
        if isinstance(value, Mapping):
            return value
        if not hasattr(value, "id") or not hasattr(value, "user_id"):
            return value

        device_type = getattr(value, "device_type", "")
        scope = getattr(value, "scope", "")
        return {
            "id": getattr(value, "id"),
            "user_id": getattr(value, "user_id"),
            "device_name": getattr(value, "device_name"),
            "device_type": getattr(device_type, "value", device_type),
            "scope": getattr(scope, "value", scope),
            "client_version": getattr(value, "client_version", None),
            "platform": getattr(value, "platform", None),
            "last_ip": getattr(value, "last_ip", None),
            "last_user_agent": getattr(value, "last_user_agent", None),
            "expires_at": getattr(value, "expires_at"),
            "last_used_at": getattr(value, "last_used_at"),
            "created_at": getattr(value, "created_at"),
            "revoked_at": getattr(value, "revoked_at", None),
        }


class 设备会话列表项信息(设备会话信息):
    """设备会话列表项响应。"""

    is_current: bool = False


class 设备登录响应(BaseModel):
    """设备登录响应。"""

    token: str
    expires_at: datetime
    session: 设备会话信息
    user: 用户信息
