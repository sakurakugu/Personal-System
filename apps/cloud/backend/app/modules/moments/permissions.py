"""动态权限判断。"""

from __future__ import annotations

from fastapi import HTTPException

from app.modules.moments.models import 动态
from app.modules.users.models import 用户, 用户角色


def 用户可否阅读动态(moment: 动态, user: 用户 | None) -> bool:
    """判断用户是否可读取动态。"""
    if moment.is_deleted:
        return False
    if user is None:
        return False
    if moment.user_id == user.id:
        return True
    if user.role == 用户角色.admin:
        return True
    return bool(moment.is_published)


def 确保动态写入权限(moment: 动态, user: 用户) -> None:
    """校验动态写权限。"""
    if moment.user_id == user.id:
        return
    if user.role == 用户角色.admin:
        return
    raise HTTPException(status_code=403, detail="无权操作该动态")
