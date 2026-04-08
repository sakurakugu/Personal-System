"""公开文件读取路由测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID
from uuid import uuid4

from fastapi import HTTPException
from starlette.responses import StreamingResponse

from app.api.public_files import get_public_file
from app.models.file import File, FilePurpose
from app.models.user import User, UserRole


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_user(*, user_id: UUID | None = None) -> User:
    """构造测试用户。"""
    return User(
        id=user_id or uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=UserRole.user,
    )


def build_scalars_result(record: object | None) -> SimpleNamespace:
    """构造支持 scalar_one_or_none 的查询结果桩。"""
    return SimpleNamespace(scalar_one_or_none=lambda: record)


class PublicFilesApiTest(unittest.IsolatedAsyncioTestCase):
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
            build_scalars_result(file_record),
        ]

        with self.assertRaises(HTTPException) as context:
            await get_public_file("owner/files/readme.pdf", access_token=None, user=None, db=db)

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
            build_scalars_result(file_record),
        ]

        with self.assertRaises(HTTPException) as context:
            await get_public_file("owner/files/readme.pdf", access_token=None, user=other_user, db=db)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "文件不存在")

    @patch("app.api.public_files.open_object_stream")
    async def test_owner_访问普通文件时返回流式响应(self, open_object_stream) -> None:
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
            build_scalars_result(file_record),
        ]
        open_object_stream.return_value = SimpleNamespace(
            chunks=iter([b"hello"]),
            content_type="application/pdf",
            content_length=5,
        )

        response = await get_public_file("owner/files/readme.pdf", access_token=None, user=owner, db=db)

        self.assertIsInstance(response, StreamingResponse)
        self.assertEqual(response.media_type, "application/pdf")
        self.assertEqual(response.headers["content-length"], "5")
        self.assertIn("filename*=UTF-8''%E8%B5%84%E6%96%99.pdf", response.headers["content-disposition"])
        open_object_stream.assert_called_once_with("owner/files/readme.pdf")


if __name__ == "__main__":
    unittest.main()
