"""UUIDv7 主键生成工具。"""

from __future__ import annotations

from typing import cast
from uuid import UUID

from uuid_utils import uuid7


def generate_uuid7() -> UUID:
    """生成 UUIDv7（时间排序）。"""
    return cast(UUID, uuid7())
