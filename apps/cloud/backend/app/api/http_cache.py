"""HTTP 条件缓存辅助工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
import hashlib
import json
from typing import Any

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse, Response

UTC时间戳起点 = datetime(1970, 1, 1, tzinfo=timezone.utc)


def 规范化HTTP日期时间(value: datetime) -> datetime:
    """将时间统一转换为 HTTP 响应头可用的 UTC 秒级时间。"""
    return value.astimezone(timezone.utc).replace(microsecond=0)


def 构建载荷ETag(payload: Any) -> str:
    """根据响应内容构造稳定的实体标签。"""
    normalized_payload = jsonable_encoder(payload)
    serialized_payload = json.dumps(
        normalized_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return f'"{hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()}"'


def 构建缓存头(
    etag: str,
    last_modified: datetime,
    *,
    cache_scope: str = "public",
    max_age: int = 300,
) -> dict[str, str]:
    """构造缓存相关响应头。"""
    return {
        "Cache-Control": f"{cache_scope}, max-age={max_age}",
        "ETag": etag,
        "Last-Modified": format_datetime(规范化HTTP日期时间(last_modified), usegmt=True),
    }


def 规范化ETag值(value: str) -> str:
    """将请求头中的 ETag 规范化为可比较的值。"""
    normalized = value.strip()
    if normalized.startswith("W/"):
        normalized = normalized[2:].strip()
    return normalized.strip('"')


def 是否未修改(
    *,
    etag: str,
    last_modified: datetime,
    if_none_match: str | None,
    if_modified_since: str | None,
) -> bool:
    """根据条件请求头判断是否可直接返回 304。"""
    normalized_etag = 规范化ETag值(etag)
    if if_none_match:
        candidates = [item.strip() for item in if_none_match.split(",") if item.strip()]
        if "*" in candidates:
            return True
        return any(规范化ETag值(candidate) == normalized_etag for candidate in candidates)

    if not if_modified_since:
        return False

    try:
        parsed_value = parsedate_to_datetime(if_modified_since)
    except (TypeError, ValueError, IndexError):
        return False

    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(tzinfo=timezone.utc)
    return parsed_value.astimezone(timezone.utc) >= 规范化HTTP日期时间(last_modified)


def 构建条件JSON响应(
    payload: Any,
    *,
    last_modified: datetime,
    if_none_match: str | None,
    if_modified_since: str | None,
    cache_scope: str = "public",
    max_age: int = 300,
) -> Response:
    """根据条件请求头返回 JSON 响应或 304 响应。"""
    etag = 构建载荷ETag(payload)
    headers = 构建缓存头(
        etag,
        last_modified,
        cache_scope=cache_scope,
        max_age=max_age,
    )
    if 是否未修改(
        etag=etag,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
    ):
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=jsonable_encoder(payload), headers=headers)
