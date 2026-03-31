"""系统运行监控服务。"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
import re
from typing import TypeAlias

from app.schemas.system import (
    SystemRequestAggregateRead,
    SystemRequestEventRead,
    SystemRuntimeSnapshotRead,
)

RECENT_WINDOW_MINUTES = 30
SLOW_REQUEST_THRESHOLD_MS = 1000.0
MAX_MONITOR_EVENTS = 100
AGGREGATE_TOP_LIMIT = 3

_recent_errors: deque[SystemRequestEventRead] = deque(maxlen=MAX_MONITOR_EVENTS)
_recent_slow_requests: deque[SystemRequestEventRead] = deque(maxlen=MAX_MONITOR_EVENTS)
RequestGroupKey: TypeAlias = tuple[str, str]
_UUID_SEGMENT_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)
_INTEGER_SEGMENT_PATTERN = re.compile(r"^\d+$")


def _normalize_datetime(value: datetime | None) -> datetime:
    """统一转换为 UTC 时间。"""
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _prune_expired(now: datetime) -> None:
    """移除超出观察窗口的历史事件。"""
    cutoff = now - timedelta(minutes=RECENT_WINDOW_MINUTES)

    while _recent_errors and _recent_errors[0].happened_at < cutoff:
        _recent_errors.popleft()

    while _recent_slow_requests and _recent_slow_requests[0].happened_at < cutoff:
        _recent_slow_requests.popleft()


def clear_monitor_events() -> None:
    """清空监控事件，用于测试。"""
    _recent_errors.clear()
    _recent_slow_requests.clear()


def normalize_request_path(path: str) -> str:
    """归一化请求路径，避免动态 ID 打散聚合结果。"""
    if not path or path == "/":
        return path or "/"

    normalized_segments: list[str] = []
    for segment in path.split("/"):
        if not segment:
            continue
        if _INTEGER_SEGMENT_PATTERN.fullmatch(segment) or _UUID_SEGMENT_PATTERN.fullmatch(segment):
            normalized_segments.append(":id")
            continue
        normalized_segments.append(segment)

    return "/" + "/".join(normalized_segments)


def record_request_event(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    happened_at: datetime | None = None,
    detail: str | None = None,
) -> None:
    """记录请求事件。"""
    event_time = _normalize_datetime(happened_at)
    _prune_expired(event_time)

    event = SystemRequestEventRead(
        method=method.upper(),
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 1),
        happened_at=event_time,
        detail=detail,
    )

    if status_code >= 500:
        _recent_errors.append(event)

    if duration_ms >= SLOW_REQUEST_THRESHOLD_MS:
        _recent_slow_requests.append(event)


def _aggregate_events(
    events: list[SystemRequestEventRead],
    *,
    limit: int,
) -> list[SystemRequestAggregateRead]:
    """按接口聚合事件。"""
    groups: dict[RequestGroupKey, list[SystemRequestEventRead]] = {}
    for event in events:
        key = (event.method, normalize_request_path(event.path))
        groups.setdefault(key, []).append(event)

    aggregates: list[SystemRequestAggregateRead] = []
    for (method, path), items in groups.items():
        sorted_items = sorted(items, key=lambda item: item.happened_at, reverse=True)
        latest = sorted_items[0]
        max_duration_ms = max(item.duration_ms for item in items)
        avg_duration_ms = round(sum(item.duration_ms for item in items) / len(items), 1)
        aggregates.append(
            SystemRequestAggregateRead(
                method=method,
                path=path,
                count=len(items),
                last_status_code=latest.status_code,
                last_happened_at=latest.happened_at,
                max_duration_ms=round(max_duration_ms, 1),
                avg_duration_ms=avg_duration_ms,
                detail=latest.detail,
            )
        )

    aggregates.sort(
        key=lambda item: (
            -item.count,
            -item.max_duration_ms,
            -item.last_happened_at.timestamp(),
        )
    )
    return aggregates[: max(1, limit)]


def get_system_runtime_snapshot(
    *,
    limit: int = 5,
    now: datetime | None = None,
) -> SystemRuntimeSnapshotRead:
    """获取最近错误和慢请求摘要。"""
    current_time = _normalize_datetime(now)
    _prune_expired(current_time)
    normalized_limit = max(1, limit)

    recent_errors = list(_recent_errors)[-normalized_limit:][::-1]
    recent_slow_requests = list(_recent_slow_requests)[-normalized_limit:][::-1]
    top_error_routes = _aggregate_events(list(_recent_errors), limit=AGGREGATE_TOP_LIMIT)
    top_slow_routes = _aggregate_events(list(_recent_slow_requests), limit=AGGREGATE_TOP_LIMIT)

    return SystemRuntimeSnapshotRead(
        recent_window_minutes=RECENT_WINDOW_MINUTES,
        slow_request_threshold_ms=SLOW_REQUEST_THRESHOLD_MS,
        error_count=len(_recent_errors),
        slow_request_count=len(_recent_slow_requests),
        top_error_routes=top_error_routes,
        top_slow_routes=top_slow_routes,
        recent_errors=recent_errors,
        recent_slow_requests=recent_slow_requests,
    )
