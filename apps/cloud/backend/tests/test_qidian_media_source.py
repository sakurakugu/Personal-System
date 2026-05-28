"""起点文娱数据源测试。"""

from __future__ import annotations

import unittest

from app.integrations.media_sources.qidian import 起点数据源


搜索页片段 = """
<div class="y-list__item" data-index="0">
  <a class="_bookWrapper_1dzax_193" href="//m.qidian.com/chapter/1010868264/0/"
     title="诡秘之主在线阅读" data-bid="1010868264">
    <div><img data-src="//bookcover.yuewen.com/qdbimg/349573/1010868264/180" alt="诡秘之主在线阅读"></div>
    <div>
      <h2 class="_searchBookName_1lmme_434"><mark>诡秘之主</mark></h2>
      <p class="_searchBookDesc_1lmme_521"><mark>诡秘之主</mark>动画已经在腾讯视频上播出。</p>
      <p class="_searchBookAuthor_1lmme_613">爱潜水的乌贼</p>
      <div class="_tags_1lmme_700"><p>玄幻</p><p>完结</p><p>446.77万字</p></div>
    </div>
  </a>
</div>
"""

详情页片段 = """
<html>
  <head>
    <meta property="og:title" content="诡秘之主" />
    <meta property="og:description" content="蒸汽与机械的浪潮中，谁能触及非凡？" />
    <meta property="og:image" content="//bookcover.yuewen.com/qdbimg/349573/1010868264/180"/>
    <meta property="og:novel:category" content="异世大陆" />
    <meta property="og:novel:author" content="爱潜水的乌贼" />
    <meta property="og:novel:book_name" content="诡秘之主" />
    <meta property="og:novel:status" content="完本" />
  </head>
</html>
"""


class 起点数据源测试(unittest.TestCase):
    """起点页面解析测试。"""

    def test_解析搜索结果会返回封面和元数据(self) -> None:
        source = 起点数据源(client=None)  # type: ignore[arg-type]

        items = source._解析搜索结果(搜索页片段)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.provider, "qidian")
        self.assertEqual(item.external_id, "1010868264")
        self.assertEqual(item.title, "诡秘之主")
        self.assertEqual(item.creators, ["爱潜水的乌贼"])
        self.assertEqual(item.genres, ["玄幻"])
        self.assertEqual(item.tags, ["完结", "446.77万字"])
        self.assertEqual(item.cover_url, "https://bookcover.yuewen.com/qdbimg/349573/1010868264/180")

    def test_解析详情会优先读取小说开放图谱元数据(self) -> None:
        source = 起点数据源(client=None)  # type: ignore[arg-type]

        item = source._解析详情("1010868264", 详情页片段)

        self.assertEqual(item.title, "诡秘之主")
        self.assertEqual(item.creators, ["爱潜水的乌贼"])
        self.assertEqual(item.summary, "蒸汽与机械的浪潮中，谁能触及非凡？")
        self.assertEqual(item.genres, ["异世大陆"])
        self.assertEqual(item.tags, ["完本"])
        self.assertEqual(item.cover_url, "https://bookcover.yuewen.com/qdbimg/349573/1010868264/180")


if __name__ == "__main__":
    unittest.main()
