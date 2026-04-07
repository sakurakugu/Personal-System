"""对象存储服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.storage_service import (
    StorageBucketMissingError,
    build_public_url,
    check_storage_health,
    ensure_storage_bucket_exists,
    fetch_object_bytes,
)


class StorageServiceTest(unittest.TestCase):
    """对象存储服务纯逻辑测试。"""

    @patch("app.services.storage_service.Minio")
    def test_存储桶存在时健康检查通过(self, minio_cls) -> None:
        client = minio_cls.return_value
        client.bucket_exists.return_value = True

        check_storage_health()

        self.assertTrue(client.bucket_exists.called)

    @patch("app.services.storage_service.Minio")
    def test_存储桶不存在时会抛出异常(self, minio_cls) -> None:
        client = minio_cls.return_value
        client.bucket_exists.return_value = False

        with self.assertRaises(StorageBucketMissingError):
            check_storage_health()

    @patch("app.services.storage_service.Minio")
    def test_确保存储桶存在时会自动创建(self, minio_cls) -> None:
        client = minio_cls.return_value
        client.bucket_exists.return_value = False

        ensure_storage_bucket_exists()

        client.make_bucket.assert_called_once()

    def test_公开链接使用站内_files_路径(self) -> None:
        self.assertEqual(
            build_public_url("user-id/object-id.avif"),
            "/files/user-id/object-id.avif",
        )

    @patch("app.services.storage_service.Minio")
    def test_读取对象内容时会返回字节与媒体类型(self, minio_cls) -> None:
        client = minio_cls.return_value
        response = client.get_object.return_value
        response.read.return_value = b"hello"
        response.headers = {"Content-Type": "image/avif"}

        content, content_type = fetch_object_bytes("user-id/object-id.avif")

        self.assertEqual(content, b"hello")
        self.assertEqual(content_type, "image/avif")
        response.close.assert_called_once()
        response.release_conn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
