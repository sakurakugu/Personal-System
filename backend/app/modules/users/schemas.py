"""用户相关 Schema。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.shared import validate_username


class UserSettingsRead(BaseModel):
    """用户设置响应。"""

    show_private_articles_on_home: bool = False


class UserSettingsUpdate(BaseModel):
    """用户设置更新请求。"""

    show_private_articles_on_home: bool | None = None


class UserRead(BaseModel):
    """用户信息公开数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    nickname: str | None = None
    email: str
    role: str
    avatar_url: str | None = None
    bio: str | None = None
    settings: UserSettingsRead
    is_active: bool
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def normalize_user_source(cls, value: Any) -> Any:
        """兼容从 User ORM 对象读取设置字段。"""
        if isinstance(value, Mapping):
            return value
        if not hasattr(value, "id") or not hasattr(value, "username"):
            return value

        settings = getattr(value, "settings", None)
        role = getattr(value, "role", "")
        return {
            "id": getattr(value, "id"),
            "username": getattr(value, "username"),
            "nickname": getattr(value, "nickname", None),
            "email": getattr(value, "email"),
            "role": getattr(role, "value", role),
            "avatar_url": getattr(value, "avatar_url", None),
            "bio": getattr(value, "bio", None),
            "settings": {
                "show_private_articles_on_home": (
                    False
                    if settings is None
                    else bool(getattr(settings, "show_private_articles_on_home", False))
                )
            },
            "is_active": getattr(value, "is_active"),
            "created_at": getattr(value, "created_at"),
        }


class UserUpdate(BaseModel):
    """用户资料更新请求。"""

    username: str | None = Field(default=None, min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    bio: str | None = None
    avatar_url: str | None = None
    settings: UserSettingsUpdate | None = None

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value: str | None) -> str | None:
        """规范化用户名。"""
        if value is None:
            return None
        return validate_username(value)


class UserCreateByAdmin(BaseModel):
    """管理员创建用户请求。"""

    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = "user"
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value: str) -> str:
        """规范化用户名。"""
        return validate_username(value)


class UserAdminUpdate(BaseModel):
    """管理员更新用户请求。"""

    username: str | None = Field(default=None, min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    role: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    settings: UserSettingsUpdate | None = None
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value: str | None) -> str | None:
        """规范化用户名。"""
        if value is None:
            return None
        return validate_username(value)


class UserPasswordReset(BaseModel):
    """管理员重置用户密码请求。"""

    password: str = Field(min_length=6, max_length=128)


class UserChangePassword(BaseModel):
    """用户修改自己密码请求。"""

    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)
