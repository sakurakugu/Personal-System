"""公开文件读取路由。"""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from minio.error import S3Error
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import StreamingResponse

from app.api.deps import (
    get_current_user_optional,
    get_user_from_access_token_optional,
)
from app.core.database import get_db
from app.models.article import ArticleImage, ArticleStatus
from app.models.file import File, FilePurpose
from app.models.user import User
from app.services.article_service import can_user_read_article
from app.services.storage_service import open_object_stream

router = APIRouter(prefix="/files", tags=["public-files"])


def build_file_response_headers(original_name: str, *, content_length: int | None) -> dict[str, str]:
    """构造文件响应头。"""
    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(original_name)}"}
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    return headers


@router.get("/{storage_key:path}")
async def get_public_file(
    storage_key: str,
    access_token: str | None = Query(default=None),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """按对象存储路径返回文件内容，并对文章图片执行权限校验。"""
    resolved_user = await get_user_from_access_token_optional(access_token, db) or user
    original_name = ""

    article_image_result = await db.execute(
        select(ArticleImage)
        .options(selectinload(ArticleImage.article))
        .where(ArticleImage.storage_key == storage_key)
    )
    article_image = article_image_result.scalar_one_or_none()
    if article_image is not None:
        article = article_image.article
        if not can_user_read_article(article, resolved_user):
            if article.status == ArticleStatus.login_required:
                raise HTTPException(status_code=401, detail="该文章需要登录后查看")
            raise HTTPException(status_code=404, detail="文件不存在")
        original_name = article_image.original_name

    else:
        file_result = await db.execute(
            select(File).where(
                File.storage_key == storage_key,
                File.purpose == FilePurpose.file,
            )
        )
        file_record = file_result.scalar_one_or_none()
        if file_record is None:
            raise HTTPException(status_code=404, detail="文件不存在")
        if resolved_user is None:
            raise HTTPException(status_code=401, detail="未登录")
        if file_record.user_id != resolved_user.id:
            raise HTTPException(status_code=404, detail="文件不存在")
        original_name = file_record.original_name

    try:
        object_stream = open_object_stream(storage_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="文件不存在") from exc
        raise HTTPException(status_code=502, detail="文件读取失败") from exc

    return StreamingResponse(
        object_stream.chunks,
        media_type=object_stream.content_type,
        headers=build_file_response_headers(original_name, content_length=object_stream.content_length),
    )
