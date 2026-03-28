"""认证相关 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.shared import validate_email_no_plus, validate_username


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username_field(cls, value: str) -> str:
        """规范化用户名。"""
        return validate_username(value)


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

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


class TokenResponse(BaseModel):
    """令牌响应。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """刷新令牌请求。"""

    refresh_token: str
