"""文件相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileRead(BaseModel):
    """文件数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    url: str
    size: int
    mime_type: str
    created_at: datetime
