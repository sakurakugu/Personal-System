"""用户相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.shared import validate_email_no_plus, validate_username


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
    show_private_articles_on_home: bool
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """用户资料更新请求。"""

    username: str | None = Field(default=None, min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    bio: str | None = None
    avatar_url: str | None = None
    show_private_articles_on_home: bool | None = None

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value: str | None) -> str | None:
        """规范化用户名。"""
        if value is None:
            return None
        return validate_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr | None) -> EmailStr | None:
        """验证邮箱格式。"""
        return validate_email_no_plus(value)


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

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> EmailStr:
        """验证邮箱格式。"""
        return validate_email_no_plus(value) or value


class UserAdminUpdate(BaseModel):
    """管理员更新用户请求。"""

    username: str | None = Field(default=None, min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    role: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    show_private_articles_on_home: bool | None = None
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value: str | None) -> str | None:
        """规范化用户名。"""
        if value is None:
            return None
        return validate_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr | None) -> EmailStr | None:
        """验证邮箱格式。"""
        return validate_email_no_plus(value)


class UserPasswordReset(BaseModel):
    """管理员重置用户密码请求。"""

    password: str = Field(min_length=6, max_length=128)


class UserChangePassword(BaseModel):
    """用户修改自己密码请求。"""

    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)
