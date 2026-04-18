"""用户 Schema 兼容入口。"""

from app.modules.users.schemas import (
    UserAdminUpdate,
    UserChangePassword,
    UserCreateByAdmin,
    UserPasswordReset,
    UserRead,
    UserSettingsRead,
    UserSettingsUpdate,
    UserUpdate,
)

__all__ = [
    "UserAdminUpdate",
    "UserChangePassword",
    "UserCreateByAdmin",
    "UserPasswordReset",
    "UserRead",
    "UserSettingsRead",
    "UserSettingsUpdate",
    "UserUpdate",
]
