"""文章响应序列化服务。"""

from __future__ import annotations

from app.modules.articles.models import 文章
from app.modules.articles.schemas import 文章列表项, 文章信息
from app.shared.storage.file_url import 签署托管文件URL, 签署文本中托管文件URL


def 构建文章读取响应(
    article: 文章,
    *,
    sign_file_urls: bool = False,
    liked: bool = False,
) -> 文章信息:
    """构造文章详情响应。"""
    response = 文章信息.model_validate(article).model_copy(update={"liked": liked})
    if not sign_file_urls:
        return response

    return response.model_copy(
        update={
            "content": 签署文本中托管文件URL(response.content),
            "cover_url": 签署托管文件URL(response.cover_url),
        }
    )


def 构建文章列表项响应(
    article: 文章,
    *,
    sign_cover_url: bool = False,
) -> 文章列表项:
    """构造文章列表项响应。"""
    response = 文章列表项.model_validate(article)
    if not sign_cover_url:
        return response

    return response.model_copy(update={"cover_url": 签署托管文件URL(response.cover_url)})
