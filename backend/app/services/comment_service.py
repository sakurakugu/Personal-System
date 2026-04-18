"""评论服务兼容入口。"""

from app.modules.comments.service import (
    build_comment_tree,
    comments_enabled,
    create_comment,
    delete_comment,
    ensure_comment_view_permission,
    get_comments_min_role,
    get_like_status,
    like_comment,
    list_comments,
    list_pending_comments,
    moderate_comment,
    unlike_comment,
)

__all__ = [
    "build_comment_tree",
    "comments_enabled",
    "create_comment",
    "delete_comment",
    "ensure_comment_view_permission",
    "get_comments_min_role",
    "get_like_status",
    "like_comment",
    "list_comments",
    "list_pending_comments",
    "moderate_comment",
    "unlike_comment",
]
