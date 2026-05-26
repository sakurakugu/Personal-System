"""文娱服务测试。"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.modules.media.service import 列出公开文娱


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


class 文娱服务测试(unittest.IsolatedAsyncioTestCase):
    """文娱服务纯逻辑测试。"""

    async def test_公开列表返回全部数据最后更新时间且不受公开状态影响(self) -> None:
        db = AsyncMock()
        公开条目 = SimpleNamespace()

        db.execute.side_effect = [
            SimpleNamespace(scalar_one_or_none=lambda: utc_dt(2026, 5, 26, 10, 59, 48)),
            SimpleNamespace(scalar=lambda: 1),
            SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [公开条目])),
        ]

        with patch(
            "app.modules.media.service.构建文娱读取",
            return_value={
                "id": str(uuid4()),
                "title": "测试条目",
                "original_title": None,
                "media_type": "anime",
                "status": "done",
                "rating": None,
                "creator": None,
                "summary": None,
                "description": None,
                "genres": [],
                "tags": [],
                "cover_file_id": None,
                "cover_file": None,
                "is_visible": True,
                "created_at": utc_dt(2026, 5, 26, 8, 0, 0),
                "updated_at": utc_dt(2026, 5, 26, 9, 0, 0),
            },
        ) as mock_build:
            response = await 列出公开文娱(
                db,
                page=1,
                page_size=12,
                media_type=None,
                status=None,
                rating=None,
                keyword="不会影响最后更新时间",
                genre=None,
                tag=None,
            )

        self.assertEqual(response.all_data_updated_at, utc_dt(2026, 5, 26, 10, 59, 48))
        self.assertEqual(response.total, 1)
        self.assertEqual(len(response.items), 1)
        mock_build.assert_called_once_with(公开条目)


if __name__ == "__main__":
    unittest.main()
