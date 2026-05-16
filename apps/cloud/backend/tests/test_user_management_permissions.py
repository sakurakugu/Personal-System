"""用户管理权限测试。"""

from __future__ import annotations

import unittest
from uuid import UUID

from fastapi import HTTPException

from app.modules.users.permissions import (
    确保删除目标允许 as _确保删除目标允许,
    确保密码重置目标允许 as _确保密码重置目标允许,
    确保更新目标允许 as _确保更新目标允许,
    获取可管理角色 as _获取可管理角色,
    解析可管理角色 as _解析可管理角色,
)
from app.modules.users.models import 用户, 用户角色
from app.utils.uuid import generate_uuid7


def build_user(role: 用户角色, *, user_id: UUID | None = None) -> 用户:
    """构造测试用户。"""
    suffix = role.value
    return 用户(
        id=user_id or generate_uuid7(),
        username=f"{suffix}_tester",
        email=f"{suffix}_tester@example.com",
        password_hash="hashed",
        role=role,
    )


class 用户管理权限测试(unittest.TestCase):
    """用户管理权限纯逻辑测试。"""

    def test_普通管理员只能管理普通用户和管理员(self) -> None:
        admin = build_user(用户角色.admin)
        self.assertEqual(_获取可管理角色(admin), (用户角色.user, 用户角色.admin))

        with self.assertRaises(HTTPException) as ctx:
            _解析可管理角色(admin, "super_admin", "管理员不能设置超级管理员角色")

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "管理员不能设置超级管理员角色")

    def test_超级管理员可以管理全部角色(self) -> None:
        super_admin = build_user(用户角色.super_admin)
        self.assertEqual(
            _获取可管理角色(super_admin),
            (用户角色.user, 用户角色.admin, 用户角色.super_admin),
        )
        self.assertEqual(
            _解析可管理角色(super_admin, "super_admin", "不应触发"),
            用户角色.super_admin,
        )

    def test_普通管理员不能修改超级管理员(self) -> None:
        admin = build_user(用户角色.admin)
        target = build_user(用户角色.super_admin)

        with self.assertRaises(HTTPException) as ctx:
            _确保更新目标允许(admin, target)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "管理员不能修改超级管理员")

    def test_超级管理员不能修改其他超级管理员但可以修改自己(self) -> None:
        super_admin = build_user(用户角色.super_admin)
        other_super_admin = build_user(用户角色.super_admin)

        with self.assertRaises(HTTPException) as ctx:
            _确保更新目标允许(super_admin, other_super_admin)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "不能修改其他超级管理员")

        _确保更新目标允许(super_admin, build_user(用户角色.super_admin, user_id=super_admin.id))

    def test_密码重置同样遵循超级管理员隔离规则(self) -> None:
        admin = build_user(用户角色.admin)
        super_admin = build_user(用户角色.super_admin)

        with self.assertRaises(HTTPException) as ctx:
            _确保密码重置目标允许(admin, super_admin)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "管理员不能重置超级管理员密码")

        _确保密码重置目标允许(
            super_admin,
            build_user(用户角色.super_admin, user_id=super_admin.id),
        )

    def test_删除用户时仍然禁止删自己和超级管理员(self) -> None:
        admin = build_user(用户角色.admin)

        with self.assertRaises(HTTPException) as self_ctx:
            _确保删除目标允许(admin, build_user(用户角色.admin, user_id=admin.id))

        self.assertEqual(self_ctx.exception.status_code, 400)
        self.assertEqual(self_ctx.exception.detail, "不能删除自己")

        with self.assertRaises(HTTPException) as super_ctx:
            _确保删除目标允许(admin, build_user(用户角色.super_admin))

        self.assertEqual(super_ctx.exception.status_code, 403)
        self.assertEqual(super_ctx.exception.detail, "管理员不能删除超级管理员")


if __name__ == "__main__":
    unittest.main()
