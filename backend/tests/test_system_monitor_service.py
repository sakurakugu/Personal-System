"""系统运行监控服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from app.services.system_monitor_service import (
    RECENT_WINDOW_MINUTES,
    SLOW_REQUEST_THRESHOLD_MS,
    clear_monitor_events,
    get_system_runtime_snapshot,
    normalize_request_path,
    record_request_event,
)


class SystemMonitorServiceTest(unittest.TestCase):
    """系统运行监控服务纯逻辑测试。"""

    def setUp(self) -> None:
        clear_monitor_events()

    def tearDown(self) -> None:
        clear_monitor_events()

    def test_会记录最近错误和慢请求(self) -> None:
        now = datetime.now(timezone.utc)
        record_request_event(
            method="get",
            path="/api/v1/test",
            status_code=502,
            duration_ms=SLOW_REQUEST_THRESHOLD_MS + 120,
            happened_at=now,
            detail="网关异常",
        )

        snapshot = get_system_runtime_snapshot(now=now)

        self.assertEqual(snapshot.error_count, 1)
        self.assertEqual(snapshot.slow_request_count, 1)
        self.assertEqual(snapshot.recent_errors[0].method, "GET")
        self.assertEqual(snapshot.recent_errors[0].detail, "网关异常")
        self.assertEqual(snapshot.recent_slow_requests[0].path, "/api/v1/test")
        self.assertEqual(snapshot.top_error_routes[0].count, 1)
        self.assertEqual(snapshot.top_slow_routes[0].path, "/api/v1/test")

    def test_会忽略窗口外的旧事件(self) -> None:
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(minutes=RECENT_WINDOW_MINUTES + 1)
        record_request_event(
            method="post",
            path="/api/v1/old",
            status_code=500,
            duration_ms=SLOW_REQUEST_THRESHOLD_MS + 10,
            happened_at=old_time,
        )

        snapshot = get_system_runtime_snapshot(now=now)

        self.assertEqual(snapshot.error_count, 0)
        self.assertEqual(snapshot.slow_request_count, 0)
        self.assertEqual(snapshot.recent_errors, [])
        self.assertEqual(snapshot.recent_slow_requests, [])

    def test_慢请求按最新优先返回(self) -> None:
        now = datetime.now(timezone.utc)
        first = now - timedelta(minutes=5)
        second = now - timedelta(minutes=1)
        record_request_event(
            method="get",
            path="/api/v1/first",
            status_code=200,
            duration_ms=SLOW_REQUEST_THRESHOLD_MS + 1,
            happened_at=first,
        )
        record_request_event(
            method="get",
            path="/api/v1/second",
            status_code=200,
            duration_ms=SLOW_REQUEST_THRESHOLD_MS + 2,
            happened_at=second,
        )

        snapshot = get_system_runtime_snapshot(now=now)

        self.assertEqual(snapshot.recent_slow_requests[0].path, "/api/v1/second")
        self.assertEqual(snapshot.recent_slow_requests[1].path, "/api/v1/first")

    def test_会按接口聚合排序(self) -> None:
        now = datetime.now(timezone.utc)
        record_request_event(
            method="get",
            path="/api/v1/users",
            status_code=500,
            duration_ms=800,
            happened_at=now - timedelta(minutes=3),
            detail="错误一",
        )
        record_request_event(
            method="get",
            path="/api/v1/users",
            status_code=502,
            duration_ms=1200,
            happened_at=now - timedelta(minutes=1),
            detail="错误二",
        )
        record_request_event(
            method="post",
            path="/api/v1/login",
            status_code=500,
            duration_ms=700,
            happened_at=now - timedelta(minutes=2),
            detail="登录失败",
        )

        snapshot = get_system_runtime_snapshot(now=now)

        self.assertEqual(snapshot.top_error_routes[0].path, "/api/v1/users")
        self.assertEqual(snapshot.top_error_routes[0].count, 2)
        self.assertEqual(snapshot.top_error_routes[0].last_status_code, 502)
        self.assertEqual(snapshot.top_error_routes[0].detail, "错误二")
        self.assertEqual(snapshot.top_error_routes[0].max_duration_ms, 1200)
        self.assertEqual(snapshot.top_error_routes[1].path, "/api/v1/login")

    def test_会归一化数字和_uuid_路径段(self) -> None:
        self.assertEqual(normalize_request_path("/api/v1/users/123"), "/api/v1/users/:id")
        self.assertEqual(
            normalize_request_path("/api/v1/files/01960f73-4b2c-7f0f-a8df-0123456789ab"),
            "/api/v1/files/:id",
        )
        self.assertEqual(normalize_request_path("/api/v1/users/profile"), "/api/v1/users/profile")

    def test_聚合时会合并不同_id_的同类接口(self) -> None:
        now = datetime.now(timezone.utc)
        record_request_event(
            method="get",
            path="/api/v1/users/123",
            status_code=500,
            duration_ms=900,
            happened_at=now - timedelta(minutes=2),
        )
        record_request_event(
            method="get",
            path="/api/v1/users/456",
            status_code=502,
            duration_ms=1100,
            happened_at=now - timedelta(minutes=1),
        )

        snapshot = get_system_runtime_snapshot(now=now)

        self.assertEqual(snapshot.top_error_routes[0].path, "/api/v1/users/:id")
        self.assertEqual(snapshot.top_error_routes[0].count, 2)
        self.assertEqual(snapshot.top_slow_routes[0].path, "/api/v1/users/:id")


if __name__ == "__main__":
    unittest.main()
