"""文件服务测试。"""

from __future__ import annotations

import io
import unittest

from PIL import Image

from app.services.file_service import prepare_upload_payload


def create_png_bytes() -> bytes:
    """构造静态 PNG 图片。"""
    image = Image.new("RGBA", (8, 8), (255, 0, 0, 255))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def create_animated_gif_bytes() -> bytes:
    """构造两帧 GIF 动图。"""
    first = Image.new("RGB", (8, 8), (255, 0, 0))
    second = Image.new("RGB", (8, 8), (0, 0, 255))
    output = io.BytesIO()
    first.save(output, format="GIF", save_all=True, append_images=[second], loop=0, duration=120)
    return output.getvalue()


class FileServiceTest(unittest.TestCase):
    """文件服务纯逻辑测试。"""

    def test_静态位图会转换为_avif(self) -> None:
        prepared = prepare_upload_payload("cover.png", "image/png", create_png_bytes())

        self.assertEqual(prepared.original_name, "cover.png")
        self.assertEqual(prepared.storage_name, "cover.avif")
        self.assertEqual(prepared.content_type, "image/avif")
        self.assertNotEqual(prepared.content[:16], create_png_bytes()[:16])

        with Image.open(io.BytesIO(prepared.content)) as converted:
            self.assertEqual(converted.format, "AVIF")
            self.assertEqual(converted.size, (8, 8))

    def test_svg_保持原格式(self) -> None:
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"></svg>'

        prepared = prepare_upload_payload("vector.svg", "image/svg+xml", svg_content)

        self.assertEqual(prepared.original_name, "vector.svg")
        self.assertEqual(prepared.storage_name, "vector.svg")
        self.assertEqual(prepared.content_type, "image/svg+xml")
        self.assertEqual(prepared.content, svg_content)

    def test_动图保持原格式(self) -> None:
        gif_content = create_animated_gif_bytes()

        prepared = prepare_upload_payload("motion.gif", "image/gif", gif_content)

        self.assertEqual(prepared.original_name, "motion.gif")
        self.assertEqual(prepared.storage_name, "motion.gif")
        self.assertEqual(prepared.content_type, "image/gif")
        self.assertEqual(prepared.content, gif_content)

    def test_空文件名图片会自动补_avif_名称(self) -> None:
        prepared = prepare_upload_payload("", "image/png", create_png_bytes())

        self.assertEqual(prepared.original_name, "image.png")
        self.assertEqual(prepared.storage_name, "image.avif")
        self.assertEqual(prepared.content_type, "image/avif")


if __name__ == "__main__":
    unittest.main()
