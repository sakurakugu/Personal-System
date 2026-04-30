"""认证共享能力。"""

from app.shared.auth.deps import get_current_user, get_current_user_optional, require_admin, require_super_admin

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_super_admin",
]
