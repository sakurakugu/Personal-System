"""评论 Schema 兼容入口。"""

from app.modules.comments.schemas import CommentCreate, CommentLikeRead, CommentModerate, CommentPendingRead, CommentRead, CommentReplyToUser

__all__ = [
    "CommentCreate",
    "CommentLikeRead",
    "CommentModerate",
    "CommentPendingRead",
    "CommentRead",
    "CommentReplyToUser",
]
