"""文娱外部导入服务测试。"""

from __future__ import annotations

import io
from types import SimpleNamespace
from typing import Any, cast
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import UploadFile
import httpx
from PIL import Image
from starlette.datastructures import Headers

from app.modules.media.external import _下载外部图片, 上传本地封面, 从外部URL导入封面
from app.modules.media.schemas import 外部封面导入请求
from app.modules.users.models import 用户
from sqlalchemy.ext.asyncio import AsyncSession


def 构造图片字节() -> bytes:
    """构造测试图片。"""
    output = io.BytesIO()
    Image.new("RGB", (24, 32), color=(200, 120, 80)).save(output, format="PNG")
    return output.getvalue()


class 假外部图片响应:
    """用于模拟 httpx 流式图片响应。"""

    def __init__(self, content: bytes, content_type: str = "image/png") -> None:
        self.headers = {"content-type": content_type}
        self._content = content

    def raise_for_status(self) -> None:
        """模拟正常状态响应。"""

    async def aiter_bytes(self):
        """按块返回图片内容。"""
        yield self._content


class 假流式请求:
    """用于模拟 httpx stream 上下文。"""

    def __init__(self, response: 假外部图片响应 | None = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error

    async def __aenter__(self) -> 假外部图片响应:
        if self._error:
            raise self._error
        if self._response is None:
            raise AssertionError("缺少模拟响应")
        return self._response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class 假外部图片客户端:
    """用于模拟 httpx AsyncClient。"""

    def __init__(self, stream_result: 假流式请求) -> None:
        self._stream_result = stream_result

    async def __aenter__(self) -> "假外部图片客户端":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def stream(self, method: str, url: str) -> 假流式请求:
        return self._stream_result


class 文娱外部导入测试(unittest.IsolatedAsyncioTestCase):
    """文娱外部导入纯逻辑测试。"""

    async def test_外部封面下载代理失败后会直连兜底(self) -> None:
        request = httpx.Request("GET", "https://example.com/cover.png")
        proxy_error = httpx.ConnectError("代理连接失败", request=request)
        direct_content = 构造图片字节()

        with (
            patch(
                "app.modules.media.external._创建外部HTTP客户端",
                return_value=假外部图片客户端(假流式请求(error=proxy_error)),
            ),
            patch(
                "app.modules.media.external._创建直连外部HTTP客户端",
                return_value=假外部图片客户端(假流式请求(response=假外部图片响应(direct_content))),
            ),
            patch("app.modules.media.external.settings.MEDIA_EXTERNAL_HTTP_PROXY", "http://127.0.0.1:10809"),
        ):
            content, content_type = await _下载外部图片("https://example.com/cover.png")

        self.assertEqual(content, direct_content)
        self.assertEqual(content_type, "image/png")

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

    async def test_上传本地封面会创建主封面资源(self) -> None:
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
        upload_file = UploadFile(
            filename="cover.png",
            file=io.BytesIO(构造图片字节()),
            headers=Headers({"content-type": "image/png"}),
        )

        with (
            patch("app.modules.media.external.get_media_or_404", AsyncMock(return_value=item)),
            patch("app.modules.media.external.构建存储键", return_value="user/media/local-cover.avif"),
            patch("app.modules.media.external.upload_bytes") as upload_mock,
            patch("app.modules.media.external.构建文娱资源读取") as build_read_mock,
        ):
            build_read_mock.side_effect = lambda asset: SimpleNamespace(id=asset.id, storage_key=asset.storage_key)
            result = await 上传本地封面(
                db,
                user,
                str(media_id),
                upload_file,
                set_primary=True,
            )

        self.assertEqual(result.storage_key, "user/media/local-cover.avif")
        self.assertIsNotNone(stored_asset)
        self.assertEqual(stored_asset.storage_key, "user/media/local-cover.avif")
        self.assertEqual(stored_asset.original_name, "cover.avif")
        self.assertTrue(stored_asset.is_primary)
        self.assertEqual(item.primary_cover_asset_id, stored_asset.id)
        upload_mock.assert_called_once()
        db.commit.assert_awaited_once()  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
