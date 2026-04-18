"""评论模型兼容入口。"""

from app.modules.comments.models import Comment, CommentLike, CommentStatus

__all__ = ["Comment", "CommentLike", "CommentStatus"]
