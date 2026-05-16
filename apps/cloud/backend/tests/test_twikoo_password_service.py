"""Twikoo 密码运维服务测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.modules.system.twikoo_password_service import (
    _写入_twikoo_数据目录,
    _计算_twikoo_管理密码存储哈希,
)


class Twikoo密码服务测试(unittest.TestCase):
    """Twikoo 密码运维服务纯逻辑测试。"""

    def test_管理密码存储哈希应为双重_md5(self) -> None:
        self.assertEqual(
            _计算_twikoo_管理密码存储哈希("233333"),
            "b896130cb4950b607f3fb892b83784bc",
        )

    def _创建空_twikoo_数据目录(self, base_dir: Path) -> None:
        db_meta = {
            "filename": str(base_dir / "db.json"),
            "collections": [
                {
                    "name": "comment",
                    "data": [],
                    "maxId": 0,
                    "dirty": False,
                },
                {
                    "name": "config",
                    "data": [],
                    "maxId": 0,
                    "dirty": False,
                },
                {
                    "name": "counter",
                    "data": [],
                    "maxId": 0,
                    "dirty": False,
                },
            ],
        }
        (base_dir / "db.json").write_text(json.dumps(db_meta, ensure_ascii=False), encoding="utf-8")
        (base_dir / "db.json.0").write_text("", encoding="utf-8")
        (base_dir / "db.json.1").write_text("", encoding="utf-8")
        (base_dir / "db.json.2").write_text("", encoding="utf-8")

    def test_可向空配置分片写入管理密码(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            数据目录 = Path(temp_dir)
            self._创建空_twikoo_数据目录(数据目录)

            _写入_twikoo_数据目录(数据目录, "hash-demo")

            config_record = json.loads((数据目录 / "db.json.1").read_text(encoding="utf-8"))
            db_meta = json.loads((数据目录 / "db.json").read_text(encoding="utf-8"))

            self.assertEqual(config_record["ADMIN_PASS"], "hash-demo")
            self.assertEqual(config_record["$loki"], 1)
            self.assertEqual(config_record["meta"]["revision"], 0)
            self.assertEqual(db_meta["collections"][1]["maxId"], 1)
            self.assertTrue(db_meta["collections"][1]["dirty"])

    def test_写入时会保留已有配置并更新修订号(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            数据目录 = Path(temp_dir)
            self._创建空_twikoo_数据目录(数据目录)
            旧记录 = {
                "ADMIN_PASS": "old-hash",
                "MAIL_SUBJECT": "demo",
                "meta": {
                    "revision": 2,
                    "created": 123,
                    "updated": 456,
                    "version": 0,
                },
                "$loki": 7,
            }
            (数据目录 / "db.json.1").write_text(json.dumps(旧记录, ensure_ascii=False), encoding="utf-8")

            _写入_twikoo_数据目录(数据目录, "new-hash")

            新记录 = json.loads((数据目录 / "db.json.1").read_text(encoding="utf-8"))
            self.assertEqual(新记录["ADMIN_PASS"], "new-hash")
            self.assertEqual(新记录["MAIL_SUBJECT"], "demo")
            self.assertEqual(新记录["$loki"], 7)
            self.assertEqual(新记录["meta"]["created"], 123)
            self.assertEqual(新记录["meta"]["revision"], 3)


if __name__ == "__main__":
    unittest.main()
