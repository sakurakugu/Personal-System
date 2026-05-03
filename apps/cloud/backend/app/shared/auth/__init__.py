"""认证共享能力。"""

from app.shared.auth.deps import get_current_user, get_current_user_optional, require_admin, require_super_admin
from app.shared.auth.device_deps import get_current_device_session, get_current_device_session_optional, require_device_scope

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_device_session",
    "get_current_device_session_optional",
    "require_admin",
    "require_device_scope",
    "require_super_admin",
]
