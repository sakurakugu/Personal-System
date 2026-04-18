"""共享认证依赖。"""

from app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_user_from_session_id,
    get_user_from_session_id_optional,
    require_admin,
    require_minimum_role,
    require_super_admin,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_user_from_session_id",
    "get_user_from_session_id_optional",
    "require_admin",
    "require_minimum_role",
    "require_super_admin",
]
