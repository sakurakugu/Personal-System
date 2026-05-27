"""文娱服务测试。"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.modules.media.service import 列出公开文娱, 列出文娱创作者建议, 列出文娱标签


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


class 文娱服务测试(unittest.IsolatedAsyncioTestCase):
    """文娱服务纯逻辑测试。"""

    async def test_创作者建议按次数和名称排序(self) -> None:
        db = AsyncMock()
        user = SimpleNamespace(id=uuid4())
        db.execute.return_value = [
            SimpleNamespace(name="Type-Moon", _mapping={"count": 3}),
            SimpleNamespace(name="京都动画", _mapping={"count": 2}),
        ]

        suggestions = await 列出文娱创作者建议(
            db,
            user,
            keyword="  moon ",
            limit=10,
        )

        self.assertEqual(
            [item.model_dump() for item in suggestions],
            [
                {"name": "Type-Moon", "count": 3},
                {"name": "京都动画", "count": 2},
            ],
        )
        db.execute.assert_awaited_once()

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

    async def test_子分类统计支持按主分类过滤(self) -> None:
        db = AsyncMock()
        user = SimpleNamespace(id=uuid4())
        db.execute.return_value = [
            SimpleNamespace(name="机战", _mapping={"count": 2}),
            SimpleNamespace(name="校园", _mapping={"count": 1}),
        ]

        response = await 列出文娱标签(
            db,
            user,
            field_name="genres",
            media_type="anime",
        )

        self.assertEqual(
            [item.model_dump() for item in response],
            [
                {"name": "机战", "count": 2},
                {"name": "校园", "count": 1},
            ],
        )
        db.execute.assert_awaited_once()

    async def test_标签统计支持按主分类过滤(self) -> None:
        db = AsyncMock()
        user = SimpleNamespace(id=uuid4())
        db.execute.return_value = [
            SimpleNamespace(name="神作", _mapping={"count": 2}),
            SimpleNamespace(name="补完", _mapping={"count": 1}),
        ]

        response = await 列出文娱标签(
            db,
            user,
            field_name="tags",
            media_type="game",
        )

        self.assertEqual(
            [item.model_dump() for item in response],
            [
                {"name": "神作", "count": 2},
                {"name": "补完", "count": 1},
            ],
        )
        db.execute.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
