"""用户公共校验兼容入口。"""

from app.modules.users.common import (
    apply_settings_update,
    ensure_email_available,
    ensure_username_available,
    ensure_username_or_email_available_for_create,
    get_user_or_404,
    normalize_nickname_input,
    normalize_username_input,
)

__all__ = [
    "apply_settings_update",
    "ensure_email_available",
    "ensure_username_available",
    "ensure_username_or_email_available_for_create",
    "get_user_or_404",
    "normalize_nickname_input",
    "normalize_username_input",
]
