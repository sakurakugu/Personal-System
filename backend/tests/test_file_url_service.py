"""文件签名服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.file_url_service import (
    build_signed_file_url,
    sign_managed_file_url,
    sign_managed_file_urls_in_text,
    verify_signed_file_request,
)


class FileUrlServiceTest(unittest.TestCase):
    """文件签名服务测试。"""

    @patch("app.services.file_url_service.time.time", return_value=1_700_000_000)
    def test_生成签名链接并校验通过(self, _mock_time) -> None:
        url = build_signed_file_url(
            "user-id/articles/demo.avif",
            query_params={"thumbnail_width": 144, "thumbnail_height": 144},
        )

        self.assertIn("/files/user-id/articles/demo.avif", url)
        self.assertIn("thumbnail_width=144", url)
        self.assertIn("thumbnail_height=144", url)
        self.assertIn("expires=1700000900", url)
        self.assertIn("signature=", url)

        self.assertTrue(
            verify_signed_file_request(
                "user-id/articles/demo.avif",
                expires_at=1_700_000_900,
                signature=url.split("signature=", 1)[1],
                query_params={"thumbnail_width": 144, "thumbnail_height": 144},
                now_timestamp=1_700_000_000,
            )
        )

    @patch("app.services.file_url_service.time.time", return_value=1_700_000_000)
    def test_过期签名会校验失败(self, _mock_time) -> None:
        url = build_signed_file_url("user-id/articles/demo.avif")
        signature = url.split("signature=", 1)[1]

        self.assertFalse(
            verify_signed_file_request(
                "user-id/articles/demo.avif",
                expires_at=1_700_000_900,
                signature=signature,
                now_timestamp=1_700_000_901,
            )
        )

    @patch("app.services.file_url_service.time.time", return_value=1_700_000_000)
    def test_会把站内文件链接改写为签名链接(self, _mock_time) -> None:
        signed = sign_managed_file_url("/files/user-id/articles/demo.avif?access_token=abc")

        self.assertIsNotNone(signed)
        assert signed is not None
        self.assertTrue(signed.startswith("/files/user-id/articles/demo.avif?"))
        self.assertNotIn("access_token=", signed)
        self.assertIn("signature=", signed)
        self.assertIn("expires=1700000900", signed)

    @patch("app.services.file_url_service.time.time", return_value=1_700_000_000)
    def test_文本中的站内文件链接会被批量签名(self, _mock_time) -> None:
        content = '![图](/files/user-id/articles/demo.avif)\n<img src="/files/user-id/articles/cover.avif">'

        signed_content = sign_managed_file_urls_in_text(content)

        self.assertEqual(signed_content.count("signature="), 2)
        self.assertNotIn("access_token=", signed_content)


if __name__ == "__main__":
    unittest.main()
