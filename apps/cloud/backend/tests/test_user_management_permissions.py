"""用户管理权限测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock
from unittest.mock import Mock
from uuid import UUID

from fastapi import HTTPException

from app.modules.users.models import 用户, 用户角色
from app.modules.users.admin import (
    _确保管理员角色变更允许,
    _确保管理员状态变更允许,
)
from app.modules.users.permissions import (
    确保删除目标允许 as _确保删除目标允许,
    确保密码重置目标允许 as _确保密码重置目标允许,
    确保更新目标允许 as _确保更新目标允许,
    获取可管理角色 as _获取可管理角色,
    解析可管理角色 as _解析可管理角色,
)
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

    def test_管理员可管理普通用户和管理员(self) -> None:
        admin = build_user(用户角色.admin)

        self.assertEqual(_获取可管理角色(admin), (用户角色.user, 用户角色.admin))
        self.assertEqual(_解析可管理角色(admin, "admin", "不应触发"), 用户角色.admin)
        self.assertEqual(_解析可管理角色(admin, "user", "不应触发"), 用户角色.user)

    def test_无效角色会被拒绝(self) -> None:
        admin = build_user(用户角色.admin)

        with self.assertRaises(HTTPException) as ctx:
            _解析可管理角色(admin, "owner", "无权设置该角色")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "无效的角色")

    def test_管理员之间可更新和重置密码(self) -> None:
        admin = build_user(用户角色.admin)
        target = build_user(用户角色.admin)

        _确保更新目标允许(admin, target)
        _确保密码重置目标允许(admin, target)

    def test_删除用户时仍然禁止删自己(self) -> None:
        admin = build_user(用户角色.admin)

        with self.assertRaises(HTTPException) as self_ctx:
            _确保删除目标允许(admin, build_user(用户角色.admin, user_id=admin.id))

        self.assertEqual(self_ctx.exception.status_code, 400)
        self.assertEqual(self_ctx.exception.detail, "不能删除自己")

        _确保删除目标允许(admin, build_user(用户角色.admin))


class 用户管理管理员唯一性测试(unittest.IsolatedAsyncioTestCase):
    """管理员唯一性规则测试。"""

    async def test_不能提升第二个管理员(self) -> None:
        db = AsyncMock()
        target = build_user(用户角色.user)

        with self.assertRaises(HTTPException) as ctx:
            await _确保管理员角色变更允许(db, target, 用户角色.admin)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "系统只允许保留一个管理员")

    async def test_不能降级唯一管理员(self) -> None:
        db = AsyncMock()
        db.execute.return_value = Mock(scalar=Mock(return_value=1))
        target = build_user(用户角色.admin)

        with self.assertRaises(HTTPException) as ctx:
            await _确保管理员角色变更允许(db, target, 用户角色.user)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "不能降级唯一管理员")

    async def test_不能停用唯一管理员(self) -> None:
        db = AsyncMock()
        db.execute.return_value = Mock(scalar=Mock(return_value=1))
        target = build_user(用户角色.admin)

        with self.assertRaises(HTTPException) as ctx:
            await _确保管理员状态变更允许(db, target, False)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "不能停用唯一管理员")


if __name__ == "__main__":
    unittest.main()
