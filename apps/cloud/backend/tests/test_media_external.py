"""文娱外部导入服务测试。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from PIL import Image
import io

from app.modules.media.external import 从外部URL导入封面
from app.modules.media.schemas import 外部封面导入请求
from app.modules.users.models import 用户
from sqlalchemy.ext.asyncio import AsyncSession


def 构造图片字节() -> bytes:
    """构造测试图片。"""
    output = io.BytesIO()
    Image.new("RGB", (24, 32), color=(200, 120, 80)).save(output, format="PNG")
    return output.getvalue()


class 文娱外部导入测试(unittest.IsolatedAsyncioTestCase):
    """文娱外部导入纯逻辑测试。"""

    async def test_外部封面本地化会创建主封面资源(self) -> None:
        db = cast(AsyncSession, SimpleNamespace(
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            rollback=AsyncMock(),
            refresh=AsyncMock(),
        ))
        user = cast(用户, SimpleNamespace(id=uuid4()))
        media_id = uuid4()
        item = SimpleNamespace(id=media_id, assets=[], primary_cover_asset_id=None)
        stored_asset: Any = None

        def add(record: object) -> None:
            nonlocal stored_asset
            stored_asset = record

        db.add.side_effect = add  # type: ignore[attr-defined]

        with (
            patch("app.modules.media.external.get_media_or_404", AsyncMock(return_value=item)),
            patch("app.modules.media.external._下载外部图片", AsyncMock(return_value=(构造图片字节(), "image/png"))),
            patch("app.modules.media.external.构建存储键", return_value="user/media/cover.avif"),
            patch("app.modules.media.external.upload_bytes") as upload_mock,
            patch("app.modules.media.external.构建文娱资源读取") as build_read_mock,
        ):
            build_read_mock.side_effect = lambda asset: SimpleNamespace(id=asset.id, storage_key=asset.storage_key)
            result = await 从外部URL导入封面(
                db,
                user,
                str(media_id),
                外部封面导入请求(
                    external_url="https://example.com/cover.png",
                    source_provider="bangumi",
                    source_asset_id="123",
                ),
            )

        self.assertEqual(result.storage_key, "user/media/cover.avif")
        self.assertIsNotNone(stored_asset)
        self.assertEqual(stored_asset.storage_key, "user/media/cover.avif")
        self.assertEqual(stored_asset.source_provider, "bangumi")
        self.assertTrue(stored_asset.is_primary)
        self.assertEqual(item.primary_cover_asset_id, stored_asset.id)
        upload_mock.assert_called_once()
        db.commit.assert_awaited_once()  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
