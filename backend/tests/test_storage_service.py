"""对象存储服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.storage_service import (
    StorageBucketMissingError,
    check_storage_health,
    ensure_storage_bucket_exists,
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


if __name__ == "__main__":
    unittest.main()
