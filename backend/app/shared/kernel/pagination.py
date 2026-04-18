"""共享分页结构。"""

from __future__ import annotations

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    """通用分页响应。"""

    items: list
    total: int
    page: int
    page_size: int
    pages: int
