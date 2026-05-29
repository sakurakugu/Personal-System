"""公开文件读取路由测试。"""

from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image
from starlette.responses import Response, StreamingResponse

from app.api.public_files import 构建原文件ETag, 构建缩略图ETag, 获取公开文件
from app.modules.articles.models import 文章, 文章图片, 文章状态
from app.modules.files.models import File, FilePurpose
from app.modules.media.models import 文娱资源, 文娱条目
from app.modules.users.models import 用户, 用户角色
from app.shared.storage.file_url import 构建签名文件URL


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_user(*, user_id: UUID | None = None) -> 用户:
    """构造测试用户。"""
    return 用户(
        id=user_id or uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=用户角色.user,
    )


def build_scalars_result(record: object | None) -> SimpleNamespace:
    """构造支持 scalar_one_or_none 的查询结果桩。"""
    return SimpleNamespace(scalar_one_or_none=lambda: record)


def build_png_bytes(width: int = 320, height: int = 180) -> bytes:
    """构造静态 PNG 图片。"""
    output = io.BytesIO()
    image = Image.new("RGB", (width, height), (24, 160, 88))
    image.save(output, format="PNG")
    return output.getvalue()


class 公开文件API测试(unittest.IsolatedAsyncioTestCase):
    """公开文件读取路由测试。"""

    async def test_普通文件未登录时拒绝访问(self) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="资料.pdf",
            storage_key="owner/files/readme.pdf",
            size=128,
            mime_type="application/pdf",
            created_at=utc_dt(2026, 4, 8, 17, 0),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]

        with self.assertRaises(HTTPException) as context:
            await 获取公开文件("owner/files/readme.pdf", user=None, db=db)

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "未登录")

    async def test_普通文件仅_owner_可读取(self) -> None:
        owner = build_user()
        other_user = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="资料.pdf",
            storage_key="owner/files/readme.pdf",
            size=128,
            mime_type="application/pdf",
            created_at=utc_dt(2026, 4, 8, 17, 5),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]

        with self.assertRaises(HTTPException) as context:
            await 获取公开文件("owner/files/readme.pdf", user=other_user, db=db)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "文件不存在")

    @patch("app.api.public_files.打开对象流")
    async def test_owner_访问普通文件时返回流式响应(self, 打开对象流) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="资料.pdf",
            storage_key="owner/files/readme.pdf",
            size=128,
            mime_type="application/pdf",
            created_at=utc_dt(2026, 4, 8, 17, 10),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]
        打开对象流.return_value = SimpleNamespace(
            chunks=iter([b"hello"]),
            content_type="application/pdf",
            content_length=5,
        )

        response = await 获取公开文件("owner/files/readme.pdf", user=owner, db=db)

        self.assertIsInstance(response, StreamingResponse)
        self.assertEqual(response.media_type, "application/pdf")
        self.assertEqual(response.headers["content-length"], "5")
        self.assertIn("etag", response.headers)
        self.assertIn("last-modified", response.headers)
        self.assertIn(
            "filename*=UTF-8''%E8%B5%84%E6%96%99.pdf", response.headers["content-disposition"]
        )
        打开对象流.assert_called_once_with("owner/files/readme.pdf")

    @patch("app.api.public_files.打开对象流")
    async def test_owner_访问普通文件命中_etag_时返回_304(self, 打开对象流) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="资料.pdf",
            storage_key="owner/files/readme.pdf",
            size=128,
            mime_type="application/pdf",
            created_at=utc_dt(2026, 4, 8, 17, 10),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]
        etag = 构建原文件ETag(
            file_record.storage_key,
            source_size=file_record.size,
            source_mime_type=file_record.mime_type,
            source_created_at=file_record.created_at,
        )

        response = await 获取公开文件(
            "owner/files/readme.pdf",
            if_none_match=etag,
            user=owner,
            db=db,
        )

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.headers["etag"], etag)
        打开对象流.assert_not_called()

    @patch("app.api.public_files.打开对象流")
    async def test_owner_访问普通文件命中_last_modified_时返回_304(self, 打开对象流) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="资料.pdf",
            storage_key="owner/files/readme.pdf",
            size=128,
            mime_type="application/pdf",
            created_at=utc_dt(2026, 4, 8, 17, 10),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]

        response = await 获取公开文件(
            "owner/files/readme.pdf",
            if_modified_since="Wed, 08 Apr 2026 17:10:00 GMT",
            user=owner,
            db=db,
        )

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 304)
        打开对象流.assert_not_called()

    @patch("app.api.public_files.获取对象字节")
    async def test_owner_访问图片缩略图时返回缩略图响应(self, 获取对象字节) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="封面.png",
            storage_key="owner/files/cover.png",
            size=1024,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 8, 17, 20),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]
        获取对象字节.return_value = (build_png_bytes(), "image/png")

        response = await 获取公开文件(
            "owner/files/cover.png",
            thumbnail_width=144,
            thumbnail_height=144,
            user=owner,
            db=db,
        )

        self.assertIsInstance(response, Response)
        self.assertEqual(response.media_type, "image/png")
        self.assertEqual(response.headers["cache-control"], "private, max-age=300")
        self.assertIn("etag", response.headers)
        self.assertIn("last-modified", response.headers)
        self.assertGreater(len(response.body), 0)
        获取对象字节.assert_called_once_with("owner/files/cover.png")

    @patch("app.api.public_files.获取对象字节")
    async def test_owner_访问图片缩略图命中_etag_时返回_304(self, 获取对象字节) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="封面.png",
            storage_key="owner/files/cover.png",
            size=1024,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 8, 17, 20),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]
        etag = 构建缩略图ETag(
            file_record.storage_key,
            source_size=file_record.size,
            source_mime_type=file_record.mime_type,
            source_created_at=file_record.created_at,
            width=144,
            height=144,
        )

        response = await 获取公开文件(
            "owner/files/cover.png",
            thumbnail_width=144,
            thumbnail_height=144,
            if_none_match=etag,
            user=owner,
            db=db,
        )

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.headers["etag"], etag)
        获取对象字节.assert_not_called()

    @patch("app.api.public_files.获取对象字节")
    async def test_owner_访问图片缩略图命中_last_modified_时返回_304(self, 获取对象字节) -> None:
        owner = build_user()
        file_record = File(
            id=uuid4(),
            user_id=owner.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="封面.png",
            storage_key="owner/files/cover.png",
            size=1024,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 8, 17, 20),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(file_record),
        ]

        response = await 获取公开文件(
            "owner/files/cover.png",
            thumbnail_width=144,
            thumbnail_height=144,
            if_modified_since="Wed, 08 Apr 2026 17:20:00 GMT",
            user=owner,
            db=db,
        )

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 304)
        获取对象字节.assert_not_called()

    @patch("app.api.public_files.打开对象流")
    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_文章图片可通过签名链接直接访问(self, _mock_time, 打开对象流) -> None:
        article = 文章(
            id=uuid4(),
            title="登录可见文章",
            slug="signed-article",
            content="![图](/files/owner/articles/cover.avif)",
            status=文章状态.login_required,
            view_count=0,
            like_count=0,
            author_id=uuid4(),
            category_id=None,
            is_deleted=False,
            deleted_at=None,
            published_at=utc_dt(2026, 4, 8, 18, 0),
            created_at=utc_dt(2026, 4, 8, 17, 50),
            last_edited_at=utc_dt(2026, 4, 8, 17, 55),
            updated_at=utc_dt(2026, 4, 8, 17, 55),
        )
        article_image = 文章图片(
            id=uuid4(),
            article_id=article.id,
            original_name="封面.avif",
            storage_key="owner/articles/cover.avif",
            size=2048,
            mime_type="image/avif",
            created_at=utc_dt(2026, 4, 8, 18, 1),
        )
        article_image.article = article
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(article_image),
        ]
        打开对象流.return_value = SimpleNamespace(
            chunks=iter([b"binary-image"]),
            content_type="image/avif",
            content_length=12,
        )
        signed_url = 构建签名文件URL("owner/articles/cover.avif")
        query = parse_qs(urlsplit(signed_url).query)

        response = await 获取公开文件(
            "owner/articles/cover.avif",
            expires=int(query["expires"][0]),
            signature=query["signature"][0],
            user=None,
            db=db,
        )

        self.assertIsInstance(response, StreamingResponse)
        self.assertEqual(response.media_type, "image/avif")
        打开对象流.assert_called_once_with("owner/articles/cover.avif")

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_已删除文章图片的签名链接对未登录用户失效(self, _mock_time) -> None:
        article = 文章(
            id=uuid4(),
            title="已删除文章",
            slug="deleted-article",
            content="![图](/files/owner/articles/cover.avif)",
            status=文章状态.public,
            view_count=0,
            like_count=0,
            author_id=uuid4(),
            category_id=None,
            is_deleted=True,
            deleted_at=utc_dt(2026, 4, 8, 18, 5),
            published_at=utc_dt(2026, 4, 8, 18, 0),
            created_at=utc_dt(2026, 4, 8, 17, 50),
            last_edited_at=utc_dt(2026, 4, 8, 17, 55),
            updated_at=utc_dt(2026, 4, 8, 17, 55),
        )
        article_image = 文章图片(
            id=uuid4(),
            article_id=article.id,
            original_name="封面.avif",
            storage_key="owner/articles/cover.avif",
            size=2048,
            mime_type="image/avif",
            created_at=utc_dt(2026, 4, 8, 18, 1),
        )
        article_image.article = article
        db = AsyncMock()
        db.execute.return_value = build_scalars_result(article_image)
        signed_url = 构建签名文件URL("owner/articles/cover.avif")
        query = parse_qs(urlsplit(signed_url).query)

        with self.assertRaises(HTTPException) as context:
            await 获取公开文件(
                "owner/articles/cover.avif",
                expires=int(query["expires"][0]),
                signature=query["signature"][0],
                user=None,
                db=db,
            )

        self.assertEqual(context.exception.status_code, 404)

    @patch("app.api.public_files.打开对象流")
    async def test_已删除文章图片作者登录后仍可预览(self, 打开对象流) -> None:
        owner = build_user()
        article = 文章(
            id=uuid4(),
            title="已删除文章",
            slug="deleted-article",
            content="![图](/files/owner/articles/cover.avif)",
            status=文章状态.private,
            view_count=0,
            like_count=0,
            author_id=owner.id,
            category_id=None,
            is_deleted=True,
            deleted_at=utc_dt(2026, 4, 8, 18, 5),
            published_at=None,
            created_at=utc_dt(2026, 4, 8, 17, 50),
            last_edited_at=utc_dt(2026, 4, 8, 17, 55),
            updated_at=utc_dt(2026, 4, 8, 17, 55),
        )
        article_image = 文章图片(
            id=uuid4(),
            article_id=article.id,
            original_name="封面.avif",
            storage_key="owner/articles/cover.avif",
            size=2048,
            mime_type="image/avif",
            created_at=utc_dt(2026, 4, 8, 18, 1),
        )
        article_image.article = article
        db = AsyncMock()
        db.execute.return_value = build_scalars_result(article_image)
        打开对象流.return_value = SimpleNamespace(
            chunks=iter([b"binary-image"]),
            content_type="image/avif",
            content_length=12,
        )

        response = await 获取公开文件("owner/articles/cover.avif", user=owner, db=db)

        self.assertIsInstance(response, StreamingResponse)
        打开对象流.assert_called_once_with("owner/articles/cover.avif")

    @patch("app.api.public_files.打开对象流")
    async def test_公开文娱封面未登录可读取并使用公开缓存(self, 打开对象流) -> None:
        owner = build_user()
        media_item = 文娱条目(
            id=uuid4(),
            user_id=owner.id,
            title="公开作品",
            media_type="anime",
            status="done",
            genres=[],
            tags=[],
            personal_tags=[],
            is_visible=True,
            is_deleted=False,
            created_at=utc_dt(2026, 5, 29, 8, 0),
            updated_at=utc_dt(2026, 5, 29, 8, 30),
        )
        media_asset = 文娱资源(
            id=uuid4(),
            user_id=owner.id,
            media_item_id=media_item.id,
            asset_type="cover",
            storage_key="owner/media/item/covers/cover.webp",
            original_name="cover.webp",
            mime_type="image/webp",
            size=1024,
            is_primary=True,
            sort_order=0,
            created_at=utc_dt(2026, 5, 29, 8, 10),
            updated_at=utc_dt(2026, 5, 29, 8, 10),
        )
        media_asset.media_item = media_item
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result(None),
            build_scalars_result(None),
            build_scalars_result(media_asset),
        ]
        打开对象流.return_value = SimpleNamespace(
            chunks=iter([b"binary-image"]),
            content_type="image/webp",
            content_length=12,
        )

        response = await 获取公开文件("owner/media/item/covers/cover.webp", user=None, db=db)

        self.assertIsInstance(response, StreamingResponse)
        self.assertEqual(response.headers["Cache-Control"], "public, max-age=300")
        打开对象流.assert_called_once_with("owner/media/item/covers/cover.webp")


if __name__ == "__main__":
    unittest.main()
