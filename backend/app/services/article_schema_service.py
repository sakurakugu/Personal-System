"""文章响应服务兼容入口。"""

from app.modules.articles.schema import build_article_list_item_response, build_article_read_response

__all__ = ["build_article_list_item_response", "build_article_read_response"]
