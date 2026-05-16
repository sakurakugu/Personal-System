"""系统运行监控。"""

from __future__ import annotations

from collections.abc import Awaitable
from datetime import datetime, timedelta, timezone
import re
from typing import TypeAlias, TypeVar, cast

from app.core.redis import get_redis
from app.modules.system.schemas import (
    系统请求聚合信息,
    系统请求事件信息,
    系统运行时快照信息,
)

RECENT_WINDOW_MINUTES = 30
SLOW_REQUEST_THRESHOLD_MS = 1000.0
MAX_MONITOR_EVENTS = 100
AGGREGATE_TOP_LIMIT = 3

_RECENT_ERRORS_KEY = "system_monitor:recent_errors"
_RECENT_SLOW_REQUESTS_KEY = "system_monitor:recent_slow_requests"
请求分组键: TypeAlias = tuple[str, str]
T = TypeVar("T")
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


def _build_cutoff(now: datetime) -> datetime:
    """构建最近窗口的截止时间。"""
    return now - timedelta(minutes=RECENT_WINDOW_MINUTES)


def _构建空快照(*, limit: int) -> 系统运行时快照信息:
    """构建空的运行时摘要。"""
    return 系统运行时快照信息(
        recent_window_minutes=RECENT_WINDOW_MINUTES,
        slow_request_threshold_ms=SLOW_REQUEST_THRESHOLD_MS,
        error_count=0,
        slow_request_count=0,
        top_error_routes=[],
        top_slow_routes=[],
        recent_errors=[],
        recent_slow_requests=[],
    )


async def _append_event(key: str, event: 系统请求事件信息) -> None:
    """向 Redis 追加监控事件。"""
    redis = await get_redis()
    await _解析_redis_结果(redis.lpush(key, event.model_dump_json()))
    await _解析_redis_结果(redis.ltrim(key, 0, MAX_MONITOR_EVENTS - 1))


async def _load_events(key: str) -> list[系统请求事件信息]:
    """从 Redis 读取监控事件。"""
    redis = await get_redis()
    payloads = await _解析_redis_结果(redis.lrange(key, 0, MAX_MONITOR_EVENTS - 1))

    events: list[系统请求事件信息] = []
    for payload in payloads:
        if not isinstance(payload, str):
            continue
        try:
            events.append(系统请求事件信息.model_validate_json(payload))
        except Exception:
            continue
    return events


def _过滤最近事件(
    events: list[系统请求事件信息],
    *,
    cutoff: datetime,
) -> list[系统请求事件信息]:
    """过滤窗口内的最近事件。"""
    return [event for event in events if event.happened_at >= cutoff]


async def 清除监控事件() -> None:
    """清空监控事件，用于测试。"""
    try:
        redis = await get_redis()
        await redis.delete(_RECENT_ERRORS_KEY, _RECENT_SLOW_REQUESTS_KEY)
    except Exception:
        return


async def _解析_redis_结果(value: Awaitable[T] | T) -> T:
    """兼容 redis 类型声明里的同步/异步联合返回值。"""
    if isinstance(value, Awaitable):
        return await cast(Awaitable[T], value)
    return value


def 规范化请求路径(path: str) -> str:
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


async def 记录请求事件(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    happened_at: datetime | None = None,
    detail: str | None = None,
) -> None:
    """记录请求事件。"""
    event = 系统请求事件信息(
        method=method.upper(),
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 1),
        happened_at=_normalize_datetime(happened_at),
        detail=detail,
    )

    try:
        if status_code >= 500:
            await _append_event(_RECENT_ERRORS_KEY, event)

        if duration_ms >= SLOW_REQUEST_THRESHOLD_MS:
            await _append_event(_RECENT_SLOW_REQUESTS_KEY, event)
    except Exception:
        return


def _aggregate_events(
    events: list[系统请求事件信息],
    *,
    limit: int,
) -> list[系统请求聚合信息]:
    """按接口聚合事件。"""
    groups: dict[请求分组键, list[系统请求事件信息]] = {}
    for event in events:
        key = (event.method, 规范化请求路径(event.path))
        groups.setdefault(key, []).append(event)

    aggregates: list[系统请求聚合信息] = []
    for (method, path), items in groups.items():
        sorted_items = sorted(items, key=lambda item: item.happened_at, reverse=True)
        latest = sorted_items[0]
        max_duration_ms = max(item.duration_ms for item in items)
        avg_duration_ms = round(sum(item.duration_ms for item in items) / len(items), 1)
        aggregates.append(
            系统请求聚合信息(
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


async def 获取系统运行时快照(
    *,
    limit: int = 5,
    now: datetime | None = None,
) -> 系统运行时快照信息:
    """获取最近错误和慢请求摘要。"""
    current_time = _normalize_datetime(now)
    cutoff = _build_cutoff(current_time)
    normalized_limit = max(1, limit)

    try:
        recent_errors_all, recent_slow_requests_all = await _load_events(_RECENT_ERRORS_KEY), await _load_events(
            _RECENT_SLOW_REQUESTS_KEY
        )
    except Exception:
        return _构建空快照(limit=normalized_limit)

    recent_errors_filtered = _过滤最近事件(recent_errors_all, cutoff=cutoff)
    recent_slow_requests_filtered = _过滤最近事件(recent_slow_requests_all, cutoff=cutoff)

    return 系统运行时快照信息(
        recent_window_minutes=RECENT_WINDOW_MINUTES,
        slow_request_threshold_ms=SLOW_REQUEST_THRESHOLD_MS,
        error_count=len(recent_errors_filtered),
        slow_request_count=len(recent_slow_requests_filtered),
        top_error_routes=_aggregate_events(recent_errors_filtered, limit=AGGREGATE_TOP_LIMIT),
        top_slow_routes=_aggregate_events(recent_slow_requests_filtered, limit=AGGREGATE_TOP_LIMIT),
        recent_errors=recent_errors_filtered[:normalized_limit],
        recent_slow_requests=recent_slow_requests_filtered[:normalized_limit],
    )
