"""当前用户资料相关服务兼容入口。"""

from app.modules.users.profile import (
    change_current_user_password,
    delete_current_user_account,
    update_current_user,
)

__all__ = [
    "change_current_user_password",
    "delete_current_user_account",
    "update_current_user",
]
