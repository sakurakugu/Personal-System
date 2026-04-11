"""邮箱工具测试。"""

from __future__ import annotations

import unittest

from app.models.user import User
from app.utils.email import build_email_identity


class EmailUtilsTest(unittest.TestCase):
    """邮箱工具纯逻辑测试。"""

    def test_谷歌邮箱会忽略点号和加号别名(self) -> None:
        self.assertEqual(build_email_identity("Foo.Bar+news@gmail.com"), "foobar@gmail.com")
        self.assertEqual(build_email_identity("foo.bar+news@googlemail.com"), "foobar@gmail.com")

    def test_非谷歌邮箱仅规范化域名大小写(self) -> None:
        self.assertEqual(
            build_email_identity("Foo.Bar+news@Example.COM"),
            "Foo.Bar+news@example.com",
        )

    def test_用户模型会自动同步邮箱判重键(self) -> None:
        user = User(username="tester", email="hello.world+tag@gmail.com", password_hash="hashed")
        self.assertEqual(user.email_identity, "helloworld@gmail.com")

        user.email = "hello.world+next@googlemail.com"
        self.assertEqual(user.email_identity, "helloworld@gmail.com")


if __name__ == "__main__":
    unittest.main()
