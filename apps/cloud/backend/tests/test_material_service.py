"""资料库模块服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.modules.materials.models import 资料, 资料状态, 资料类型
from app.modules.materials.service import (
    应用资料删除状态,
    应用资料状态,
    恢复资料删除状态,
    构建资料读取,
)
from app.utils.uuid import generate_uuid7


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_material(**overrides: object) -> 资料:
    """构造测试用资料库条目。"""
    defaults: dict[str, object] = {
        "id": generate_uuid7(),
        "user_id": generate_uuid7(),
        "type": 资料类型.text,
        "title": "测试资料",
        "content_text": "测试内容",
        "note": "测试备注",
        "status": 资料状态.active,
        "archived_at": None,
        "is_deleted": False,
        "deleted_at": None,
        "created_at": utc_dt(2026, 4, 12, 8, 0),
        "updated_at": utc_dt(2026, 4, 12, 8, 0),
        "assets": [],
        "material_tags": [],
    }
    defaults.update(overrides)
    return 资料(**defaults)


class 资料服务测试(unittest.TestCase):
    """资料库模块纯逻辑测试。"""

    def test_软删除会保留原有业务状态(self) -> None:
        material = build_material(status=资料状态.archived, archived_at=utc_dt(2026, 4, 10, 9, 0))

        应用资料删除状态(material, now=utc_dt(2026, 4, 12, 10, 0))

        self.assertEqual(material.status, 资料状态.archived)
        self.assertEqual(material.archived_at, utc_dt(2026, 4, 10, 9, 0))
        self.assertTrue(material.is_deleted)
        self.assertEqual(material.deleted_at, utc_dt(2026, 4, 12, 10, 0))

    def test_恢复软删除不会改变原有业务状态(self) -> None:
        material = build_material(
            status=资料状态.active,
            is_deleted=True,
            deleted_at=utc_dt(2026, 4, 12, 10, 0),
        )

        恢复资料删除状态(material)

        self.assertEqual(material.status, 资料状态.active)
        self.assertFalse(material.is_deleted)
        self.assertIsNone(material.deleted_at)

    def test_归档与删除字段会出现在响应中(self) -> None:
        material = build_material()
        应用资料状态(material, 资料状态.archived, now=utc_dt(2026, 4, 11, 9, 0))
        应用资料删除状态(material, now=utc_dt(2026, 4, 12, 10, 0))

        data = 构建资料读取(material)

        self.assertEqual(data.status, "archived")
        self.assertEqual(data.archived_at, utc_dt(2026, 4, 11, 9, 0))
        self.assertTrue(data.is_deleted)
        self.assertEqual(data.deleted_at, utc_dt(2026, 4, 12, 10, 0))


if __name__ == "__main__":
    unittest.main()
