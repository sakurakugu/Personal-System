"""用户权限规则。"""

from __future__ import annotations

from fastapi import HTTPException

from app.models.user import User, UserRole


def parse_user_role(role_value: str) -> UserRole:
    """解析用户角色字符串。"""
    try:
        return UserRole(role_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的角色") from exc


def get_manageable_roles(admin: User) -> tuple[UserRole, ...]:
    """返回当前管理员可管理的角色范围。"""
    if admin.role == UserRole.super_admin:
        return (UserRole.user, UserRole.admin, UserRole.super_admin)
    return (UserRole.user, UserRole.admin)


def parse_manageable_role(admin: User, role_value: str, detail: str) -> UserRole:
    """解析并校验管理员可操作的角色。"""
    role = parse_user_role(role_value)
    if role not in get_manageable_roles(admin):
        raise HTTPException(status_code=403, detail=detail)
    return role


def ensure_update_target_allowed(admin: User, target: User) -> None:
    """校验当前管理员是否可以修改目标用户资料。"""
    if admin.role == UserRole.admin and target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能修改超级管理员")
    if target.role == UserRole.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="不能修改其他超级管理员")


def ensure_password_reset_target_allowed(admin: User, target: User) -> None:
    """校验当前管理员是否可以重置目标用户密码。"""
    if admin.role == UserRole.admin and target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能重置超级管理员密码")
    if target.role == UserRole.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="不能修改其他超级管理员")


def ensure_delete_target_allowed(admin: User, target: User) -> None:
    """校验当前管理员是否可以删除目标用户。"""
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    if admin.role == UserRole.admin and target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能删除超级管理员")
    if target.role == UserRole.super_admin:
        raise HTTPException(status_code=403, detail="不能删除超级管理员")
