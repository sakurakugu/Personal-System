"""软删除共享类型。"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class 可软删除对象(Protocol):
    """包含软删除状态字段的对象。"""

    is_deleted: bool
    deleted_at: datetime | None
