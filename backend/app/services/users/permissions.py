"""用户权限兼容入口。"""

from app.modules.users.permissions import (
    ensure_delete_target_allowed,
    ensure_password_reset_target_allowed,
    ensure_update_target_allowed,
    get_manageable_roles,
    parse_manageable_role,
    parse_user_role,
)

__all__ = [
    "ensure_delete_target_allowed",
    "ensure_password_reset_target_allowed",
    "ensure_update_target_allowed",
    "get_manageable_roles",
    "parse_manageable_role",
    "parse_user_role",
]
