"""认证相关 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, field_validator

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

