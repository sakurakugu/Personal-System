"""用户管理权限测试。"""

from __future__ import annotations

import unittest
from uuid import UUID

from fastapi import HTTPException

from app.api.v1.users import (
    _ensure_delete_target_allowed,
    _ensure_password_reset_target_allowed,
    _ensure_update_target_allowed,
    _get_manageable_roles,
    _parse_manageable_role,
)
from app.models.user import User, UserRole
from app.utils.uuid import generate_uuid7


def build_user(role: UserRole, *, user_id: UUID | None = None) -> User:
    """构造测试用户。"""
    suffix = role.value
    return User(
        id=user_id or generate_uuid7(),
        username=f"{suffix}_tester",
        email=f"{suffix}_tester@example.com",
        password_hash="hashed",
        role=role,
    )


class UserManagementPermissionsTest(unittest.TestCase):
    """用户管理权限纯逻辑测试。"""

    def test_普通管理员只能管理普通用户和管理员(self) -> None:
        admin = build_user(UserRole.admin)
        self.assertEqual(_get_manageable_roles(admin), (UserRole.user, UserRole.admin))

        with self.assertRaises(HTTPException) as ctx:
            _parse_manageable_role(admin, "super_admin", "管理员不能设置超级管理员角色")

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "管理员不能设置超级管理员角色")

    def test_超级管理员可以管理全部角色(self) -> None:
        super_admin = build_user(UserRole.super_admin)
        self.assertEqual(
            _get_manageable_roles(super_admin),
            (UserRole.user, UserRole.admin, UserRole.super_admin),
        )
        self.assertEqual(
            _parse_manageable_role(super_admin, "super_admin", "不应触发"),
            UserRole.super_admin,
        )

    def test_普通管理员不能修改超级管理员(self) -> None:
        admin = build_user(UserRole.admin)
        target = build_user(UserRole.super_admin)

        with self.assertRaises(HTTPException) as ctx:
            _ensure_update_target_allowed(admin, target)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "管理员不能修改超级管理员")

    def test_超级管理员不能修改其他超级管理员但可以修改自己(self) -> None:
        super_admin = build_user(UserRole.super_admin)
        other_super_admin = build_user(UserRole.super_admin)

        with self.assertRaises(HTTPException) as ctx:
            _ensure_update_target_allowed(super_admin, other_super_admin)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "不能修改其他超级管理员")

        _ensure_update_target_allowed(super_admin, build_user(UserRole.super_admin, user_id=super_admin.id))

    def test_密码重置同样遵循超级管理员隔离规则(self) -> None:
        admin = build_user(UserRole.admin)
        super_admin = build_user(UserRole.super_admin)

        with self.assertRaises(HTTPException) as ctx:
            _ensure_password_reset_target_allowed(admin, super_admin)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "管理员不能重置超级管理员密码")

        _ensure_password_reset_target_allowed(
            super_admin,
            build_user(UserRole.super_admin, user_id=super_admin.id),
        )

    def test_删除用户时仍然禁止删自己和超级管理员(self) -> None:
        admin = build_user(UserRole.admin)

        with self.assertRaises(HTTPException) as self_ctx:
            _ensure_delete_target_allowed(admin, build_user(UserRole.admin, user_id=admin.id))

        self.assertEqual(self_ctx.exception.status_code, 400)
        self.assertEqual(self_ctx.exception.detail, "不能删除自己")

        with self.assertRaises(HTTPException) as super_ctx:
            _ensure_delete_target_allowed(admin, build_user(UserRole.super_admin))

        self.assertEqual(super_ctx.exception.status_code, 403)
        self.assertEqual(super_ctx.exception.detail, "管理员不能删除超级管理员")


if __name__ == "__main__":
    unittest.main()
