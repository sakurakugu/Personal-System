"""Schema 共享工具。"""

from __future__ import annotations

from pydantic import BaseModel

已注销后缀 = "（已注销）"


def validate_username(value: str) -> str:
    """规范化并校验用户名。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("用户名不能为空")
    if 已注销后缀 in normalized:
        raise ValueError(f"用户名不能包含保留标记 {已注销后缀}")
    return normalized


class PaginatedResponse(BaseModel):
    """通用分页响应。"""

    items: list
    total: int
    page: int
    page_size: int
    pages: int
