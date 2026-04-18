"""用户服务兼容入口。"""

from app.modules.users.cleanup import build_deleted_comment_name, delete_user_with_cleanup

__all__ = ["build_deleted_comment_name", "delete_user_with_cleanup"]
