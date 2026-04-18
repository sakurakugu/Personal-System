"""文章搜索服务兼容入口。"""

from app.modules.articles.search import build_article_search_clause

__all__ = ["build_article_search_clause"]
