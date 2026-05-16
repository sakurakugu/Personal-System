"""文件响应构造。"""

from __future__ import annotations

from app.modules.articles.models import 文章图片
from app.modules.files.models import File, FilePurpose
from app.modules.files.schemas import FileRead, FileSearchItemRead
from app.modules.moments.models import 动态图片
from app.shared.storage.file_url import 构建公开文件URL, 构建签名文件URL

根目录名称 = "全部文件"
文章图片目录名称 = "文章图片"
动态图片目录名称 = "动态图片"


def 构建文章图片路径(article_title: str) -> str:
    """构造文章图片在资源管理器中的展示路径。"""
    normalized_title = article_title.strip() or "未命名文章"
    return " / ".join([根目录名称, 文章图片目录名称, normalized_title])


def 构建动态图片路径(moment_title: str) -> str:
    """构造动态图片在资源管理器中的展示路径。"""
    normalized_title = moment_title.strip() or "未命名动态"
    return " / ".join([根目录名称, 动态图片目录名称, normalized_title])


def 构建稳定缩略图URL(storage_key: str, mime_type: str) -> str | None:
    """为可缩略图图片生成稳定缩略图链接。"""
    if not mime_type.startswith("image/") or mime_type == "image/svg+xml":
        return None
    return 构建公开文件URL(
        storage_key,
        query_params={
            "thumbnail_width": 144,
            "thumbnail_height": 144,
        },
    )


def 构建文件读取(record: File) -> FileRead:
    """将普通文件模型转换为统一的文件响应。"""
    return FileRead(
        id=record.id,
        folder_id=record.folder_id,
        purpose=record.purpose,
        original_name=record.original_name,
        url=构建签名文件URL(record.storage_key),
        thumbnail_url=构建稳定缩略图URL(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
    )


def 构建文章图片文件读取(record: 文章图片) -> FileRead:
    """将文章图片模型转换为统一的文件响应。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return FileRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=record.original_name,
        url=构建签名文件URL(record.storage_key),
        thumbnail_url=构建稳定缩略图URL(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        article_id=record.article_id,
        article_title=article_title,
    )


def 构建动态图片文件读取(record: 动态图片) -> FileRead:
    """将动态图片模型转换为统一的文件响应。"""
    moment_title = record.moment.title if record.moment is not None and record.moment.title is not None else "未命名动态"
    return FileRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.moment_image,
        original_name=record.original_name,
        url=构建签名文件URL(record.storage_key),
        thumbnail_url=构建稳定缩略图URL(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        moment_id=record.moment_id,
        moment_title=moment_title,
    )


def 构建搜索文件读取(record: File, *, path: str) -> FileSearchItemRead:
    """将普通文件模型转换为搜索结果项。"""
    return FileSearchItemRead(
        id=record.id,
        folder_id=record.folder_id,
        purpose=record.purpose,
        original_name=record.original_name,
        url=构建签名文件URL(record.storage_key),
        thumbnail_url=构建稳定缩略图URL(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=path,
    )


def 构建文章图片搜索读取(record: 文章图片) -> FileSearchItemRead:
    """将文章图片模型转换为搜索结果项。"""
    article_title = record.article.title if record.article is not None else "未命名文章"
    return FileSearchItemRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.article_image,
        original_name=record.original_name,
        url=构建签名文件URL(record.storage_key),
        thumbnail_url=构建稳定缩略图URL(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=构建文章图片路径(article_title),
        article_id=record.article_id,
        article_title=article_title,
    )


def 构建动态图片搜索读取(record: 动态图片) -> FileSearchItemRead:
    """将动态图片模型转换为搜索结果项。"""
    moment_title = record.moment.title if record.moment is not None and record.moment.title is not None else "未命名动态"
    return FileSearchItemRead(
        id=record.id,
        folder_id=None,
        purpose=FilePurpose.moment_image,
        original_name=record.original_name,
        url=构建签名文件URL(record.storage_key),
        thumbnail_url=构建稳定缩略图URL(record.storage_key, record.mime_type),
        size=record.size,
        mime_type=record.mime_type,
        created_at=record.created_at,
        path=构建动态图片路径(moment_title),
        moment_id=record.moment_id,
        moment_title=moment_title,
    )


def 排序资源管理器文件(records: list[FileRead]) -> list[FileRead]:
    """统一排序普通文件与文章图片。"""
    return sorted(records, key=lambda item: (item.original_name.lower(), -item.created_at.timestamp()))
