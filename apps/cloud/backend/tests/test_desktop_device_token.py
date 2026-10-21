"""桌面小工具设备令牌签发测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.modules.auth import device_api
from app.modules.auth.device_models import 设备会话范围, 设备会话类型
from app.modules.auth.device_schemas import 桌面端令牌创建请求
from app.modules.auth.device_service import 吊销同名桌面设备会话


def utc_dt(year: int, month: int, day: int) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, tzinfo=timezone.utc)


def build_device_session(*, device_name: str, revoked_at: datetime | None = None):
    """构造用于校验吊销逻辑的设备会话。"""
    return SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        device_name=device_name,
        device_type=设备会话类型.desktop,
        scope=设备会话范围.full_client,
        client_version=None,
        platform=None,
        last_ip=None,
        last_user_agent=None,
        expires_at=utc_dt(2026, 11, 1),
        last_used_at=utc_dt(2026, 10, 1),
        created_at=utc_dt(2026, 10, 1),
        revoked_at=revoked_at,
    )


class FakeScalarResult:
    """模拟 SQLAlchemy Result 的 scalars().all() 调用。"""

    def __init__(self, sessions: list[SimpleNamespace]) -> None:
        self._sessions = sessions

    def scalars(self):
        return self

    def all(self):
        return self._sessions


class FakeDb:
    """只实现 execute 的模拟数据库会话。"""

    def __init__(self, sessions: list[SimpleNamespace]) -> None:
        self._sessions = sessions
        self.executed = 0

    async def execute(self, _statement):
        self.executed += 1
        return FakeScalarResult(self._sessions)


class 桌面端令牌Schema测试(unittest.TestCase):
    """请求模型默认值测试。"""

    def test_默认设备名称(self) -> None:
        body = 桌面端令牌创建请求()
        self.assertEqual(body.device_name, "Personal System 桌面小工具")

    def test_设备名称会去掉首尾空格(self) -> None:
        body = 桌面端令牌创建请求(device_name="  我的小工具  ")
        self.assertEqual(body.device_name, "我的小工具")


class 吊销同名桌面设备会话测试(unittest.IsolatedAsyncioTestCase):
    """同名旧会话吊销逻辑测试。"""

    async def test_只吊销未吊销的同名桌面会话(self) -> None:
        active_session = build_device_session(device_name="Personal System 桌面小工具")
        revoked_session = build_device_session(
            device_name="Personal System 桌面小工具",
            revoked_at=utc_dt(2026, 9, 1),
        )
        db = FakeDb([active_session, revoked_session])

        revoked_count = await 吊销同名桌面设备会话(
            db,
            user_id=uuid4(),
            device_name="Personal System 桌面小工具",
        )

        self.assertEqual(revoked_count, 1)
        self.assertIsNotNone(active_session.revoked_at)
        self.assertEqual(revoked_session.revoked_at, utc_dt(2026, 9, 1))


class 创建桌面端令牌接口测试(unittest.IsolatedAsyncioTestCase):
    """令牌签发接口测试。"""

    async def test_返回设备令牌与会话信息(self) -> None:
        user_id = uuid4()
        session = build_device_session(device_name="Personal System 桌面小工具")
        session.user_id = user_id
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        request = SimpleNamespace(client=None, headers={})
        current_user = SimpleNamespace(id=user_id)

        with patch.object(
            device_api,
            "吊销同名桌面设备会话",
            new=AsyncMock(return_value=2),
        ) as revoke_mock, patch.object(
            device_api,
            "创建设备会话",
            new=AsyncMock(
                return_value=SimpleNamespace(token="pst_dev_demo", session=session)
            ),
        ) as create_mock:
            response = await device_api.创建桌面端令牌(
                桌面端令牌创建请求(),
                request,
                current_user,
                object(),
            )

        self.assertEqual(response.token, "pst_dev_demo")
        self.assertEqual(response.session.device_name, "Personal System 桌面小工具")
        self.assertEqual(response.session.device_type, "desktop")
        self.assertEqual(response.session.scope, "full_client")
        revoke_mock.assert_awaited_once()
        self.assertEqual(
            revoke_mock.await_args.kwargs["device_name"],
            "Personal System 桌面小工具",
        )
        self.assertEqual(create_mock.await_args.kwargs["device_type"], 设备会话类型.desktop)
        self.assertEqual(create_mock.await_args.kwargs["scope"], 设备会话范围.full_client)
        self.assertIsInstance(expires_at, datetime)


if __name__ == "__main__":
    unittest.main()
