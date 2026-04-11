"""友链服务测试。"""

from __future__ import annotations

import unittest

from app.services.friend_link_service import contains_backlink, normalize_domain


class FriendLinkServiceTest(unittest.TestCase):
    """友链检测逻辑测试。"""

    def test_会从网址中提取规范域名片段(self) -> None:
        self.assertEqual(normalize_domain("https://www.Example.com/blog/"), "example.com/blog")

    def test_包含本站链接时会识别成功(self) -> None:
        html = """
        <html>
          <body>
            <a href="https://sakurakugu.top/friends">友情链接</a>
          </body>
        </html>
        """

        self.assertTrue(contains_backlink(html, "https://www.sakurakugu.top"))

    def test_www与裸域会视为同一站点(self) -> None:
        html = """
        <html>
          <body>
            <a href="https://www.sakurakugu.top/friends">友情链接</a>
          </body>
        </html>
        """

        self.assertTrue(contains_backlink(html, "https://sakurakugu.top"))

    def test_不包含本站链接时会识别失败(self) -> None:
        html = """
        <html>
          <body>
            <a href="https://example.com">Example</a>
          </body>
        </html>
        """

        self.assertFalse(contains_backlink(html, "https://www.sakurakugu.top"))


if __name__ == "__main__":
    unittest.main()
