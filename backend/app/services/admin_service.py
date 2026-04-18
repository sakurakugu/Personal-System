"""后台管理服务兼容入口。"""

from app.modules.system.service import (
    get_system_status,
    read_system_settings,
    read_system_settings_with_updated_at,
    update_system_settings,
    validate_comments_min_role,
)

__all__ = [
    "get_system_status",
    "read_system_settings",
    "read_system_settings_with_updated_at",
    "update_system_settings",
    "validate_comments_min_role",
]
