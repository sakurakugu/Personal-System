"""收藏模块服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.modules.collections.models import Collection, CollectionStatus, CollectionType
from app.modules.collections.service import (
    应用归档状态,
    应用收藏删除状态,
    构建收藏读取,
    恢复收藏删除状态,
)
from app.utils.uuid import generate_uuid7


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_collection(**overrides: object) -> Collection:
    """构造测试用收藏对象。"""
    defaults: dict[str, object] = {
        "id": generate_uuid7(),
        "user_id": generate_uuid7(),
        "type": CollectionType.text,
        "title": "测试收藏",
        "content_text": "测试内容",
        "note": "测试备注",
        "status": CollectionStatus.ready,
        "archived_at": None,
        "is_deleted": False,
        "deleted_at": None,
        "created_at": utc_dt(2026, 4, 12, 8, 0),
        "updated_at": utc_dt(2026, 4, 12, 8, 0),
        "assets": [],
        "collection_tags": [],
    }
    defaults.update(overrides)
    return Collection(**defaults)


class CollectionServiceTest(unittest.TestCase):
    """收藏模块纯逻辑测试。"""

    def test_软删除会保留原有业务状态(self) -> None:
        collection = build_collection(status=CollectionStatus.archived, archived_at=utc_dt(2026, 4, 10, 9, 0))

        应用收藏删除状态(collection, now=utc_dt(2026, 4, 12, 10, 0))

        self.assertEqual(collection.status, CollectionStatus.archived)
        self.assertEqual(collection.archived_at, utc_dt(2026, 4, 10, 9, 0))
        self.assertTrue(collection.is_deleted)
        self.assertEqual(collection.deleted_at, utc_dt(2026, 4, 12, 10, 0))

    def test_恢复软删除不会改变原有业务状态(self) -> None:
        collection = build_collection(
            status=CollectionStatus.processing,
            is_deleted=True,
            deleted_at=utc_dt(2026, 4, 12, 10, 0),
        )

        恢复收藏删除状态(collection)

        self.assertEqual(collection.status, CollectionStatus.processing)
        self.assertFalse(collection.is_deleted)
        self.assertIsNone(collection.deleted_at)

    def test_归档与删除字段会出现在响应中(self) -> None:
        collection = build_collection()
        应用归档状态(collection, CollectionStatus.archived, now=utc_dt(2026, 4, 11, 9, 0))
        应用收藏删除状态(collection, now=utc_dt(2026, 4, 12, 10, 0))

        data = 构建收藏读取(collection)

        self.assertEqual(data.status, "archived")
        self.assertEqual(data.archived_at, utc_dt(2026, 4, 11, 9, 0))
        self.assertTrue(data.is_deleted)
        self.assertEqual(data.deleted_at, utc_dt(2026, 4, 12, 10, 0))


if __name__ == "__main__":
    unittest.main()
