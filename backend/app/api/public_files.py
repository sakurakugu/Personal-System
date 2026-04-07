"""公开文件读取路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from minio.error import S3Error
from starlette.responses import Response

from app.services.storage_service import fetch_object_bytes

router = APIRouter(prefix="/files", tags=["public-files"])


@router.get("/{storage_key:path}")
def get_public_file(storage_key: str):
    """按对象存储路径返回公开文件内容。"""
    try:
        content, content_type = fetch_object_bytes(storage_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="文件不存在") from exc
        raise HTTPException(status_code=502, detail="文件读取失败") from exc

    return Response(content=content, media_type=content_type)
