"""系统设置服务测试。"""

from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.modules.system.schemas import (
    HealthCheckRead,
    HealthComponentStatus,
    SystemRuntimeSnapshotRead,
)
from app.modules.system.service import (
    get_system_status,
    读取系统设置_with_updated_at,
)


class SystemServiceTest(unittest.IsolatedAsyncioTestCase):
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

        payload, _ = await 读取系统设置_with_updated_at(db)

        self.assertFalse(payload.register_enabled)
        self.assertFalse(payload.comments_enabled)
        self.assertTrue(payload.comments_hidden)

    async def test_状态缓存未过期时直接返回缓存(self) -> None:
        import app.modules.system.service as service_module

        cached = service_module.SystemStatus(
            cpu_percent=1,
            memory_total_gb=2,
            memory_used_gb=1,
            memory_percent=50,
            disk_total_gb=10,
            disk_used_gb=3,
            disk_percent=30,
            uptime_seconds=100,
            health=HealthCheckRead(
                status="healthy",
                checked_at=datetime.now(timezone.utc),
                database=HealthComponentStatus(status="healthy"),
                redis=HealthComponentStatus(status="healthy"),
                minio=HealthComponentStatus(status="healthy"),
            ),
            runtime=SystemRuntimeSnapshotRead(
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

        refreshed = service_module.SystemStatus(
            cpu_percent=2,
            memory_total_gb=4,
            memory_used_gb=2,
            memory_percent=50,
            disk_total_gb=20,
            disk_used_gb=4,
            disk_percent=20,
            uptime_seconds=200,
            health=HealthCheckRead(
                status="healthy",
                checked_at=datetime.now(timezone.utc),
                database=HealthComponentStatus(status="healthy"),
                redis=HealthComponentStatus(status="healthy"),
                minio=HealthComponentStatus(status="healthy"),
            ),
            runtime=SystemRuntimeSnapshotRead(
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
