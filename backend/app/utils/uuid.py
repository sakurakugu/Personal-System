"""UUIDv7 主键生成工具。

此模块提供 UUIDv7 生成功能，UUIDv7 是时间排序的 UUID，
相比 UUIDv4 具有更好的数据库索引性能。
"""

from __future__ import annotations

from uuid import UUID

try:
    from uuid import uuid7 as _stdlib_uuid7

    # 生产端使用，3.14 版本
    def generate_uuid7() -> UUID:
        """
        生成 UUIDv7（时间排序）。

        UUIDv7 包含时间戳信息，生成的 UUID 按时间顺序排列，
        适合用作数据库主键，可以提高插入性能和索引效率。

        Returns:
            UUID: 生成的 UUIDv7 对象

        Example:
            >>> user_id = generate_uuid7()
            >>> print(user_id)
            018f5c7a-8c6b-7e8f-9a0b-1c2d3e4f5a6b
        """
        return _stdlib_uuid7()
except ImportError:
    from uuid_utils import uuid7 as uuid7_fallback

    # 开发端使用，当前是 3.13 版本，等下升级
    def generate_uuid7() -> UUID:
        """
        生成 UUIDv7（时间排序）。

        UUIDv7 包含时间戳信息，生成的 UUID 按时间顺序排列，
        适合用作数据库主键，可以提高插入性能和索引效率。

        Returns:
            UUID: 生成的 UUIDv7 对象

        Example:
            >>> user_id = generate_uuid7()
            >>> print(user_id)
            018f5c7a-8c6b-7e8f-9a0b-1c2d3e4f5a6b
        """
        return UUID(str(uuid7_fallback()))
