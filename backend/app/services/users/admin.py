"""管理员用户管理服务兼容入口。"""

from app.modules.users.admin import (
    create_user_by_admin,
    delete_user_by_admin,
    list_users_by_admin,
    reset_user_password_by_admin,
    update_user_by_admin,
)

__all__ = [
    "create_user_by_admin",
    "delete_user_by_admin",
    "list_users_by_admin",
    "reset_user_password_by_admin",
    "update_user_by_admin",
]
