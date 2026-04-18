"""文章响应序列化服务。"""

from __future__ import annotations

from app.modules.articles.models import Article
from app.modules.articles.schemas import ArticleListItem, ArticleRead
from app.services.file_url_service import sign_managed_file_url, sign_managed_file_urls_in_text


def build_article_read_response(article: Article, *, sign_file_urls: bool = False) -> ArticleRead:
    """构造文章详情响应。"""
    response = ArticleRead.model_validate(article)
    if not sign_file_urls:
        return response

    return response.model_copy(
        update={
            "content": sign_managed_file_urls_in_text(response.content),
            "cover_url": sign_managed_file_url(response.cover_url),
        }
    )


def build_article_list_item_response(article: Article, *, sign_cover_url: bool = False) -> ArticleListItem:
    """构造文章列表项响应。"""
    response = ArticleListItem.model_validate(article)
    if not sign_cover_url:
        return response

    return response.model_copy(update={"cover_url": sign_managed_file_url(response.cover_url)})
