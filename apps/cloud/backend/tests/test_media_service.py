"""文娱服务测试。"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import cast
import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.modules.media.models import 文娱资源
from app.modules.media.service import (
    构建文娱资源读取,
    列出公开文娱,
    列出文娱创作者建议,
    列出文娱标签,
    应用文娱删除状态,
    恢复文娱删除状态,
)
from app.modules.users.models import 用户


def utc_dt(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0
) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


class 文娱服务测试(unittest.IsolatedAsyncioTestCase):
    """文娱服务纯逻辑测试。"""

    async def test_文娱删除状态可恢复(self) -> None:
        item = SimpleNamespace(is_deleted=False, deleted_at=None)
        deleted_time = utc_dt(2026, 5, 29, 12, 30)

        应用文娱删除状态(item, now=deleted_time)

        self.assertTrue(item.is_deleted)
        self.assertEqual(item.deleted_at, deleted_time)

        恢复文娱删除状态(item)

        self.assertFalse(item.is_deleted)
        self.assertIsNone(item.deleted_at)

    async def test_创作者建议按次数和名称排序(self) -> None:
        db = AsyncMock()
        user = cast(用户, SimpleNamespace(id=uuid4()))
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
                "personal_tags": [],
                "release_date": None,
                "primary_cover_asset_id": None,
                "primary_cover_asset": None,
                "assets": [],
                "external_sources": [],
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
                personal_tag=None,
            )

        self.assertEqual(response.all_data_updated_at, utc_dt(2026, 5, 26, 10, 59, 48))
        self.assertEqual(response.total, 1)
        self.assertEqual(len(response.items), 1)
        mock_build.assert_called_once_with(公开条目, 使用公开文件URL=True)

    async def test_公开文娱资源使用稳定公开缩略图地址(self) -> None:
        asset_id = uuid4()
        media_id = uuid4()
        asset = SimpleNamespace(
            id=asset_id,
            media_item_id=media_id,
            asset_type="cover",
            storage_key="owner/media/item/covers/cover.webp",
            external_url=None,
            thumbnail_url=None,
            source_provider=None,
            source_asset_id=None,
            original_name="cover.webp",
            mime_type="image/webp",
            width=800,
            height=1200,
            size=2048,
            attribution=None,
            license=None,
            is_primary=True,
            sort_order=0,
            created_at=utc_dt(2026, 5, 26, 8, 0, 0),
            updated_at=utc_dt(2026, 5, 26, 9, 0, 0),
        )

        response = 构建文娱资源读取(cast("文娱资源", asset), 使用公开文件URL=True)

        self.assertEqual(
            response.thumbnail_url,
            "/files/owner/media/item/covers/cover.webp?thumbnail_height=240&thumbnail_width=180&v=1779786000",
        )
        self.assertEqual(response.url, "/files/owner/media/item/covers/cover.webp?v=1779786000")
        self.assertEqual(response.preview_url, response.url)

    async def test_子分类统计支持按主分类过滤(self) -> None:
        db = AsyncMock()
        user = cast(用户, SimpleNamespace(id=uuid4()))
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
        user = cast(用户, SimpleNamespace(id=uuid4()))
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
