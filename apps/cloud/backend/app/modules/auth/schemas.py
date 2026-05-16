"""认证相关 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.kernel.validation import 校验用户名


class 登录请求(BaseModel):
    """登录请求。"""

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def 校验用户名字段(cls, value: str) -> str:
        """规范化用户名。"""
        return 校验用户名(value)


class 注册请求(BaseModel):
    """注册请求。"""

    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def 校验用户名字段(cls, value: str) -> str:
        """规范化用户名。"""
        return 校验用户名(value)
