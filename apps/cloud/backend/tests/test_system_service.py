"""系统设置服务测试。"""

from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.modules.system.schemas import (
    健康检查信息,
    健康组件状态,
    系统运行时快照信息,
)
from app.modules.system.service import (
    get_system_status,
    读取系统设置含更新时间,
)


class 系统服务测试(unittest.IsolatedAsyncioTestCase):
    """系统设置服务测试。"""

    def tearDown(self) -> None:
        import app.modules.system.service as service_module

        service_module._cached_status = None
        service_module._cached_at = 0.0

    async def test_未配置时注册默认关闭(self) -> None:
        db = AsyncMock()
        result = Mock()
        scalars = Mock()
        scalars.all.return_value = []
        result.scalars.return_value = scalars
        db.execute.return_value = result

        payload, _ = await 读取系统设置含更新时间(db)

        self.assertFalse(payload.register_enabled)
        self.assertFalse(payload.comments_enabled)
        self.assertTrue(payload.comments_hidden)

    async def test_状态缓存未过期时直接返回缓存(self) -> None:
        import app.modules.system.service as service_module

        cached = service_module.系统状态(
            cpu_percent=1,
            memory_total_gb=2,
            memory_used_gb=1,
            memory_percent=50,
            disk_total_gb=10,
            disk_used_gb=3,
            disk_percent=30,
            uptime_seconds=100,
            health=健康检查信息(
                status="healthy",
                checked_at=datetime.now(timezone.utc),
                database=健康组件状态(status="healthy"),
                redis=健康组件状态(status="healthy"),
                minio=健康组件状态(status="healthy"),
            ),
            runtime=系统运行时快照信息(
                recent_window_minutes=30,
                slow_request_threshold_ms=1000,
            ),
        )
        service_module._cached_status = cached
        service_module._cached_at = 1.0

        with patch("app.modules.system.service.time.monotonic", return_value=10.0):
            with patch("app.modules.system.service.刷新系统状态缓存", AsyncMock()) as refresh_mock:
                result = await get_system_status()

        self.assertIs(result, cached)
        refresh_mock.assert_not_awaited()

    async def test_状态缓存过期时会刷新(self) -> None:
        import app.modules.system.service as service_module

        refreshed = service_module.系统状态(
            cpu_percent=2,
            memory_total_gb=4,
            memory_used_gb=2,
            memory_percent=50,
            disk_total_gb=20,
            disk_used_gb=4,
            disk_percent=20,
            uptime_seconds=200,
            health=健康检查信息(
                status="healthy",
                checked_at=datetime.now(timezone.utc),
                database=健康组件状态(status="healthy"),
                redis=健康组件状态(status="healthy"),
                minio=健康组件状态(status="healthy"),
            ),
            runtime=系统运行时快照信息(
                recent_window_minutes=30,
                slow_request_threshold_ms=1000,
            ),
        )
        service_module._cached_status = None
        service_module._cached_at = 0.0

        with patch("app.modules.system.service.time.monotonic", return_value=100.0):
            with patch(
                "app.modules.system.service.刷新系统状态缓存",
                AsyncMock(return_value=refreshed),
            ) as refresh_mock:
                result = await get_system_status()

        self.assertIs(result, refreshed)
        refresh_mock.assert_awaited_once_with(force=True)


if __name__ == "__main__":
    unittest.main()
