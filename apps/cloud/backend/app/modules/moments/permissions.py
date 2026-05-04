"""动态权限判断。"""

from __future__ import annotations

from fastapi import HTTPException

from app.modules.moments.models import Moment
from app.modules.users.models import User


def can_user_read_moment(moment: Moment, user: User | None) -> bool:
    """判断用户是否可读取动态。"""
    if moment.is_deleted:
        return False
    if user is None:
        return False
    if moment.user_id == user.id:
        return True
    if user.role.value in ("admin", "super_admin"):
        return True
    return bool(moment.is_published)


def ensure_moment_write_permission(moment: Moment, user: User) -> None:
    """校验动态写权限。"""
    if moment.user_id == user.id:
        return
    if user.role.value in ("admin", "super_admin"):
        return
    raise HTTPException(status_code=403, detail="无权操作该动态")
