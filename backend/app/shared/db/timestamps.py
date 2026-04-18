"""数据库时间工具。"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)
