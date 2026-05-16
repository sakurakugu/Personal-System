"""首页 Feed 流 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.modules.articles.schemas import 文章列表项
from app.modules.moments.schemas import 动态公开信息


class FeedItemRead(BaseModel):
    """首页 Feed 条目响应。"""

    type: Literal["article", "moment"]
    source_id: UUID
    published_at: datetime
    article: 文章列表项 | None = None
    moment: 动态公开信息 | None = None
