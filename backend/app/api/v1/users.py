"""用户路由兼容入口。"""

from app.modules.users.api import router
from app.modules.users.permissions import (
    ensure_delete_target_allowed as _ensure_delete_target_allowed,
    ensure_password_reset_target_allowed as _ensure_password_reset_target_allowed,
    ensure_update_target_allowed as _ensure_update_target_allowed,
    get_manageable_roles as _get_manageable_roles,
    parse_manageable_role as _parse_manageable_role,
)

__all__ = [
    "_ensure_delete_target_allowed",
    "_ensure_password_reset_target_allowed",
    "_ensure_update_target_allowed",
    "_get_manageable_roles",
    "_parse_manageable_role",
    "router",
]
