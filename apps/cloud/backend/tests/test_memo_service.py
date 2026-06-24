"""备忘录模块服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.modules.memos.models import 备忘录, 备忘录来源, 备忘录状态
from app.modules.memos.service import (
    应用备忘录删除状态,
    应用备忘录状态,
    恢复备忘录删除状态,
    提取备忘录标题,
    提取备忘录链接,
    标记备忘录已转换,
    构建备忘录读取,
)
from app.utils.uuid import generate_uuid7


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_memo(**overrides: object) -> 备忘录:
    """构造测试用备忘录对象。"""
    defaults: dict[str, object] = {
        "id": generate_uuid7(),
        "user_id": generate_uuid7(),
        "content": "第一行标题\n正文内容",
        "status": 备忘录状态.inbox,
        "source": 备忘录来源.manual,
        "converted_to_type": None,
        "converted_to_id": None,
        "archived_at": None,
        "deleted_at": None,
        "created_at": utc_dt(2026, 6, 1, 8, 0),
        "updated_at": utc_dt(2026, 6, 1, 8, 0),
    }
    defaults.update(overrides)
    return 备忘录(**defaults)


class 备忘录服务测试(unittest.TestCase):
    """备忘录模块纯逻辑测试。"""

    def test_归档会写入归档时间(self) -> None:
        memo = build_memo()

        应用备忘录状态(memo, 备忘录状态.archived, now=utc_dt(2026, 6, 1, 10, 0))

        self.assertEqual(memo.status, 备忘录状态.archived)
        self.assertEqual(memo.archived_at, utc_dt(2026, 6, 1, 10, 0))
        self.assertIsNone(memo.deleted_at)

    def test_软删除会标记为废弃并保留删除时间(self) -> None:
        memo = build_memo()

        应用备忘录删除状态(memo, now=utc_dt(2026, 6, 1, 11, 0))

        self.assertEqual(memo.status, 备忘录状态.dropped)
        self.assertIsNone(memo.archived_at)
        self.assertEqual(memo.deleted_at, utc_dt(2026, 6, 1, 11, 0))

    def test_恢复软删除会回到待整理(self) -> None:
        memo = build_memo(status=备忘录状态.dropped, deleted_at=utc_dt(2026, 6, 1, 11, 0))

        恢复备忘录删除状态(memo)

        self.assertEqual(memo.status, 备忘录状态.inbox)
        self.assertIsNone(memo.archived_at)
        self.assertIsNone(memo.deleted_at)

    def test_转换会标记已处理和目标(self) -> None:
        memo = build_memo()
        target_id = generate_uuid7()

        标记备忘录已转换(memo, "collection", target_id)

        self.assertEqual(memo.status, 备忘录状态.processed)
        self.assertEqual(memo.converted_to_type, "collection")
        self.assertEqual(memo.converted_to_id, target_id)

    def test_从正文提取标题和链接(self) -> None:
        content = "\n  https://example.com/a  \n后续正文"

        self.assertEqual(提取备忘录标题(content), "https://example.com/a")
        self.assertEqual(提取备忘录链接(content), "https://example.com/a")

    def test_响应包含转换字段(self) -> None:
        target_id = generate_uuid7()
        memo = build_memo(converted_to_type="todo", converted_to_id=target_id)

        data = 构建备忘录读取(memo)

        self.assertEqual(data.status, "inbox")
        self.assertEqual(data.source, "manual")
        self.assertEqual(data.converted_to_type, "todo")
        self.assertEqual(data.converted_to_id, target_id)


if __name__ == "__main__":
    unittest.main()
