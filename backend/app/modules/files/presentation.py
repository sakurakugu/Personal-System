"""文件响应构造。"""

from __future__ import annotations

from app.modules.articles.models import ArticleImage
from app.modules.files.models import File, FilePurpose
from app.modules.files.schemas import FileRead, FileSearchItemRead
from app.services.file_url_service import build_public_file_url, build_signed_file_url

根目录名称 = "全部文件"
文章图片目录名称 = "文章图片"


def build_article_image_path(article_title: str) -> str:
    """构造文章图片在资源管理器中的展示路径。"""
    normalized_title = article_title.strip() or "未命名文章"
    return " / ".join([根目录名称, 文章图片目录名称, normalized_title])


def build_stable_thumbnail_url(storage_key: str, mime_type: str) -> str | None:
    """为可缩略图图片生成稳定缩略图链接。"""
    if not mime_type.startswith("image/") or mime_type == "image/svg+xml":
        return None
    return build_public_file_url(
        storage_key,
        query_params={
            "thumbnail_width": 144,
            "thumbnail_height": 144,
        },
    )


def build_file_read(record: File) -> FileRead:
    """将普通文件模型转换为统一的文件响应。"""
    return FileRead(
        id=record.id,
        folder_id=record.folder_id,
        purpose=record.purpose,
        original_name=record.original_name,
        url=build_signed_file_url(record.storage_key),
        thumbnail_url=build_stable_thumbnail_url(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
    )


def build_article_image_file_read(record: ArticleImage) -> FileRead:
    """将文章图片模型转换为统一的文件响应。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return FileRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=record.original_name,
        url=build_signed_file_url(record.storage_key),
        thumbnail_url=build_stable_thumbnail_url(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        article_id=record.article_id,
        article_title=article_title,
    )


def build_search_file_read(record: File, *, path: str) -> FileSearchItemRead:
    """将普通文件模型转换为搜索结果项。"""
    return FileSearchItemRead(
        id=record.id,
        folder_id=record.folder_id,
        purpose=record.purpose,
        original_name=record.original_name,
        url=build_signed_file_url(record.storage_key),
        thumbnail_url=build_stable_thumbnail_url(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=path,
    )


def build_article_image_search_read(record: ArticleImage) -> FileSearchItemRead:
    """将文章图片模型转换为搜索结果项。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return FileSearchItemRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=record.original_name,
        url=build_signed_file_url(record.storage_key),
        thumbnail_url=build_stable_thumbnail_url(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=build_article_image_path(article_title),
        article_id=record.article_id,
        article_title=article_title,
    )


def sort_explorer_files(records: list[FileRead]) -> list[FileRead]:
    """统一排序普通文件与文章图片。"""
    return sorted(records, key=lambda item: (item.original_name.lower(), -item.created_at.timestamp()))
