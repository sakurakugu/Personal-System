"""评论相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.article import ArticleListItem
from app.schemas.user import UserRead


class CommentCreate(BaseModel):
    """创建评论请求。"""

    article_id: UUID
    content: str = Field(min_length=1)
    parent_id: UUID | None = None
    guest_name: str | None = None


class CommentReplyToUser(BaseModel):
    """评论回复目标用户信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    nickname: str | None = None
    guest_name: str | None = None


class CommentRead(BaseModel):
    """评论数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_id: UUID
    user_id: UUID | None = None
    guest_name: str | None = None
    parent_id: UUID | None = None
    content: str
    status: str
    like_count: int = 0
    is_liked: bool = False
    created_at: datetime
    user: UserRead | None = None
    reply_to_user: CommentReplyToUser | None = None
    replies: list["CommentRead"] = []


class CommentModerate(BaseModel):
    """评论审核请求。"""

    status: str


class CommentLikeRead(BaseModel):
    """评论点赞响应。"""

    comment_id: str
    user_id: UUID | None = None
    is_liked: bool
    like_count: int


class CommentPendingRead(BaseModel):
    """待审核评论响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_id: UUID
    content: str
    guest_name: str | None = None
    created_at: datetime
    user: UserRead | None = None
    article: ArticleListItem | None = None


CommentRead.model_rebuild()
