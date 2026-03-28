"""首页 Feed 流 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.article import ArticleListItem
from app.schemas.moment import MomentPublicRead


class FeedItemRead(BaseModel):
    """首页 Feed 条目响应。"""

    type: Literal["article", "moment"]
    source_id: UUID
    published_at: datetime
    article: ArticleListItem | None = None
    moment: MomentPublicRead | None = None
