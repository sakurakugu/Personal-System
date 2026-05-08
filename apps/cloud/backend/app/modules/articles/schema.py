"""文章响应序列化服务。"""

from __future__ import annotations

from app.modules.articles.models import Article
from app.modules.articles.schemas import ArticleListItem, ArticleRead
from app.shared.storage.file_url import 签署托管文件URL, 签署文本中托管文件URL


def 构建文章读取响应(
    article: Article,
    *,
    sign_file_urls: bool = False,
    liked: bool = False,
) -> ArticleRead:
    """构造文章详情响应。"""
    response = ArticleRead.model_validate(article).model_copy(update={"liked": liked})
    if not sign_file_urls:
        return response

    return response.model_copy(
        update={
            "content": 签署文本中托管文件URL(response.content),
            "cover_url": 签署托管文件URL(response.cover_url),
        }
    )


def 构建文章列表项响应(
    article: Article,
    *,
    sign_cover_url: bool = False,
) -> ArticleListItem:
    """构造文章列表项响应。"""
    response = ArticleListItem.model_validate(article)
    if not sign_cover_url:
        return response

    return response.model_copy(update={"cover_url": 签署托管文件URL(response.cover_url)})
