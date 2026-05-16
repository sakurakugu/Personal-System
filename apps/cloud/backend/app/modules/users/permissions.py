"""用户权限规则。"""

from __future__ import annotations

from fastapi import HTTPException

from app.modules.users.models import 用户, 用户角色


def 解析用户角色(role_value: str) -> 用户角色:
    """解析用户角色字符串。"""
    try:
        return 用户角色(role_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的角色") from exc


def 获取可管理角色(admin: 用户) -> tuple[用户角色, ...]:
    """返回当前管理员可管理的角色范围。"""
    if admin.role == 用户角色.super_admin:
        return (用户角色.user, 用户角色.admin, 用户角色.super_admin)
    return (用户角色.user, 用户角色.admin)


def 解析可管理角色(admin: 用户, role_value: str, detail: str) -> 用户角色:
    """解析并校验管理员可操作的角色。"""
    role = 解析用户角色(role_value)
    if role not in 获取可管理角色(admin):
        raise HTTPException(status_code=403, detail=detail)
    return role


def 确保更新目标允许(admin: 用户, target: 用户) -> None:
    """校验当前管理员是否可以修改目标用户资料。"""
    if admin.role == 用户角色.admin and target.role == 用户角色.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能修改超级管理员")
    if target.role == 用户角色.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="不能修改其他超级管理员")


def 确保密码重置目标允许(admin: 用户, target: 用户) -> None:
    """校验当前管理员是否可以重置目标用户密码。"""
    if admin.role == 用户角色.admin and target.role == 用户角色.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能重置超级管理员密码")
    if target.role == 用户角色.super_admin and target.id != admin.id:
        raise HTTPException(status_code=403, detail="不能修改其他超级管理员")


def 确保删除目标允许(admin: 用户, target: 用户) -> None:
    """校验当前管理员是否可以删除目标用户。"""
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    if admin.role == 用户角色.admin and target.role == 用户角色.super_admin:
        raise HTTPException(status_code=403, detail="管理员不能删除超级管理员")
    if target.role == 用户角色.super_admin:
        raise HTTPException(status_code=403, detail="不能删除超级管理员")
