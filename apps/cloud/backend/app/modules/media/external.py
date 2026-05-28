"""文娱外部数据导入服务。"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import time
from typing import Any

from fastapi import HTTPException, UploadFile
import httpx
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.integrations.media_sources.base import 外部作品候选
from app.integrations.media_sources.registry import 数据源类型
from app.modules.files.upload_preparation import 是否为图片上传, 准备上传载荷
from app.modules.media.models import 文娱资源, 文娱外部来源, 文娱条目
from app.modules.media.schemas import (
    外部封面导入请求,
    外部文娱导入请求,
    外部文娱候选,
    外部文娱搜索响应,
    文娱资源信息,
    文娱条目信息,
)
from app.modules.media.service import get_media_or_404, 构建文娱读取, 构建文娱资源读取
from app.modules.users.models import 用户
from app.shared.db.timestamps import utcnow
from app.shared.kernel.config import settings
from app.shared.storage.client import 构建存储键, 尽力删除对象, upload_bytes

logger = logging.getLogger(__name__)
默认外部请求头 = {"User-Agent": "personal-system/1.0"}
最大文娱封面上传字节数 = 10 * 1024 * 1024


def _创建外部HTTP客户端(timeout: httpx.Timeout) -> httpx.AsyncClient:
    """创建文娱外部请求客户端，并将代理限制在文娱外部数据源范围内。"""
    proxy = settings.MEDIA_EXTERNAL_HTTP_PROXY.strip() or None
    return httpx.AsyncClient(
        timeout=timeout,
        headers=默认外部请求头,
        follow_redirects=True,
        proxy=proxy,
        trust_env=False,
    )


def _创建直连外部HTTP客户端(timeout: httpx.Timeout) -> httpx.AsyncClient:
    """创建不使用代理的文娱外部请求客户端。"""
    return httpx.AsyncClient(
        timeout=timeout,
        headers=默认外部请求头,
        follow_redirects=True,
        trust_env=False,
    )


def _按代理策略获取数据源(
    proxied_client: httpx.AsyncClient,
    direct_client: httpx.AsyncClient,
    provider: str | None,
):
    """按数据源代理策略创建文娱外部数据源。"""
    source_types = [source_type for source_type in 数据源类型 if provider is None or source_type.provider == provider.strip().lower()]
    return [source_type(proxied_client if source_type.use_proxy else direct_client) for source_type in source_types]


def _缓存键(*parts: str) -> str:
    """构建外部数据缓存键。"""
    raw = "\n".join(parts)
    return "media:external:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _读取缓存(key: str) -> Any | None:
    """读取 Redis 缓存，失败时静默降级。"""
    try:
        redis = await get_redis()
        cached = await redis.get(key)
        return json.loads(cached) if cached else None
    except Exception:
        logger.debug("读取文娱外部缓存失败，已降级", exc_info=True)
        return None


async def _写入缓存(key: str, value: Any) -> None:
    """写入 Redis 缓存，失败时静默降级。"""
    try:
        redis = await get_redis()
        await redis.setex(
            key,
            settings.MEDIA_EXTERNAL_CACHE_TTL_SECONDS,
            json.dumps(value, ensure_ascii=False, default=str),
        )
    except Exception:
        logger.debug("写入文娱外部缓存失败，已降级", exc_info=True)


def _候选转响应(item: 外部作品候选) -> 外部文娱候选:
    """将集成层候选转换成 API 响应。"""
    return 外部文娱候选.model_validate(item.model_dump())


async def 搜索外部文娱(keyword: str, media_type: str | None = None, provider: str | None = None) -> 外部文娱搜索响应:
    """搜索外部文娱作品。"""
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return 外部文娱搜索响应(items=[])

    cache_key = _缓存键("search", normalized_keyword, media_type or "", provider or "")
    cached = await _读取缓存(cache_key)
    if cached is not None:
        return 外部文娱搜索响应.model_validate(cached)

    timeout = httpx.Timeout(settings.MEDIA_EXTERNAL_REQUEST_TIMEOUT_SECONDS)
    async with _创建外部HTTP客户端(timeout) as proxied_client, _创建直连外部HTTP客户端(timeout) as direct_client:
        sources = _按代理策略获取数据源(proxied_client, direct_client, provider)
        available_sources = [source for source in sources if source is not None and source.available]

        async def run_source(source) -> list[外部作品候选]:
            start = time.perf_counter()
            try:
                items = await source.search(normalized_keyword, media_type)
                logger.info(
                    "文娱外部搜索完成 provider=%s keyword=%s media_type=%s elapsed_ms=%s count=%s",
                    source.provider,
                    normalized_keyword,
                    media_type,
                    int((time.perf_counter() - start) * 1000),
                    len(items),
                )
                return items
            except Exception:
                logger.warning(
                    "文娱外部搜索失败 provider=%s keyword=%s media_type=%s use_proxy=%s",
                    source.provider,
                    normalized_keyword,
                    media_type,
                    source.use_proxy,
                    exc_info=True,
                )
                return []

        results: list[list[外部作品候选]] = await asyncio.gather(*(run_source(source) for source in available_sources))

    seen: set[tuple[str, str]] = set()
    items: list[外部文娱候选] = []
    for source_items in results:
        for item in source_items:
            key = (item.provider, item.external_id)
            if key in seen:
                continue
            seen.add(key)
            items.append(_候选转响应(item))
    response = 外部文娱搜索响应(items=items[:48])
    await _写入缓存(cache_key, response.model_dump(mode="json"))
    return response


async def 获取外部文娱详情(provider: str, external_id: str) -> 外部文娱候选:
    """读取外部文娱详情。"""
    cache_key = _缓存键("detail", provider, external_id)
    cached = await _读取缓存(cache_key)
    if cached is not None:
        return 外部文娱候选.model_validate(cached)

    timeout = httpx.Timeout(settings.MEDIA_EXTERNAL_REQUEST_TIMEOUT_SECONDS)
    async with _创建外部HTTP客户端(timeout) as proxied_client, _创建直连外部HTTP客户端(timeout) as direct_client:
        source = next(iter(_按代理策略获取数据源(proxied_client, direct_client, provider)), None)
        if source is None:
            raise HTTPException(status_code=404, detail="外部数据源不存在")
        if not source.available:
            raise HTTPException(status_code=400, detail="外部数据源未配置")
        start = time.perf_counter()
        try:
            detail = await source.get_detail(external_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail="外部详情读取失败") from exc
        logger.info(
            "文娱外部详情读取完成 provider=%s external_id=%s elapsed_ms=%s",
            provider,
            external_id,
            int((time.perf_counter() - start) * 1000),
        )
    response = _候选转响应(detail)
    await _写入缓存(cache_key, response.model_dump(mode="json"))
    return response


def _解析图片尺寸(content: bytes) -> tuple[int | None, int | None]:
    """读取图片尺寸。"""
    try:
        with Image.open(io.BytesIO(content)) as image:
            return image.width, image.height
    except (UnidentifiedImageError, OSError, ValueError):
        return None, None


async def _下载外部图片(url: str) -> tuple[bytes, str]:
    """下载外部图片并限制大小。"""
    start = time.perf_counter()
    max_bytes = settings.MEDIA_EXTERNAL_IMAGE_MAX_BYTES
    timeout = httpx.Timeout(settings.MEDIA_EXTERNAL_REQUEST_TIMEOUT_SECONDS)
    async with _创建外部HTTP客户端(timeout) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > max_bytes:
                    raise HTTPException(status_code=413, detail="外部封面文件过大")
    logger.info(
        "文娱外部封面下载完成 url=%s size=%s mime=%s elapsed_ms=%s",
        url,
        len(content),
        content_type,
        int((time.perf_counter() - start) * 1000),
    )
    return bytes(content), content_type or "application/octet-stream"


async def 从外部URL导入封面(
    db: AsyncSession,
    user: 用户,
    media_id: str,
    body: 外部封面导入请求,
) -> 文娱资源信息:
    """从外部 URL 下载并本地化封面。"""
    item = await get_media_or_404(db, user, media_id)
    content, content_type = await _下载外部图片(body.external_url)
    filename = body.original_name or body.external_url.rsplit("/", 1)[-1] or "cover"
    if not 是否为图片上传(filename, content_type):
        raise HTTPException(status_code=400, detail="外部封面不是可识别的图片")

    source_width, source_height = _解析图片尺寸(content)
    if source_width is None or source_height is None:
        raise HTTPException(status_code=400, detail="外部封面图片内容无效")

    prepared = 准备上传载荷(
        filename=filename,
        content_type=content_type,
        content=content,
        compress_static_images=True,
    )
    storage_key = 构建存储键(user.id, prepared.storage_name, directory=f"media/{item.id}/covers")
    upload_bytes(storage_key=storage_key, content=prepared.content, content_type=prepared.content_type)
    converted_width, converted_height = _解析图片尺寸(prepared.content)
    logger.info(
        "文娱外部封面转换完成 media_id=%s before_size=%s after_size=%s storage_key=%s",
        item.id,
        len(content),
        len(prepared.content),
        storage_key,
    )

    if body.set_primary:
        for asset in item.assets or []:
            if asset.asset_type == "cover":
                asset.is_primary = False

    asset = 文娱资源(
        user_id=user.id,
        media_item_id=item.id,
        asset_type="cover",
        storage_key=storage_key,
        external_url=body.external_url,
        source_provider=body.source_provider,
        source_asset_id=body.source_asset_id,
        original_name=prepared.original_name,
        mime_type=prepared.content_type,
        width=converted_width or source_width,
        height=converted_height or source_height,
        size=len(prepared.content),
        attribution=body.attribution,
        license=body.license,
        is_primary=body.set_primary,
        imported_at=utcnow(),
    )
    db.add(asset)
    try:
        await db.flush()
        if body.set_primary:
            item.primary_cover_asset_id = asset.id
        await db.commit()
    except Exception:
        await db.rollback()
        尽力删除对象(storage_key)
        raise
    await db.refresh(asset)
    return 构建文娱资源读取(asset)


async def 上传本地封面(
    db: AsyncSession,
    user: 用户,
    media_id: str,
    file: UploadFile,
    *,
    set_primary: bool,
) -> 文娱资源信息:
    """上传本地封面并设为文娱资源。"""
    item = await get_media_or_404(db, user, media_id)
    content = await file.read()
    if len(content) > 最大文娱封面上传字节数:
        raise HTTPException(status_code=413, detail="封面文件过大（最大 10MB）")

    filename = file.filename or "cover"
    content_type = file.content_type or ""
    if not 是否为图片上传(filename, content_type):
        raise HTTPException(status_code=400, detail="封面只允许上传图片文件")

    prepared = 准备上传载荷(
        filename=filename,
        content_type=content_type,
        content=content,
        compress_static_images=True,
    )
    converted_width, converted_height = _解析图片尺寸(prepared.content)
    storage_key = 构建存储键(user.id, prepared.storage_name, directory=f"media/{item.id}/covers")
    upload_bytes(storage_key=storage_key, content=prepared.content, content_type=prepared.content_type)
    logger.info(
        "文娱本地封面上传完成 media_id=%s filename=%s before_size=%s after_size=%s storage_key=%s",
        item.id,
        filename,
        len(content),
        len(prepared.content),
        storage_key,
    )

    if set_primary:
        for asset in item.assets or []:
            if asset.asset_type == "cover":
                asset.is_primary = False

    asset = 文娱资源(
        user_id=user.id,
        media_item_id=item.id,
        asset_type="cover",
        storage_key=storage_key,
        original_name=prepared.original_name,
        mime_type=prepared.content_type,
        width=converted_width,
        height=converted_height,
        size=len(prepared.content),
        is_primary=set_primary,
        imported_at=utcnow(),
    )
    db.add(asset)
    try:
        await db.flush()
        if set_primary:
            item.primary_cover_asset_id = asset.id
        await db.commit()
    except Exception:
        await db.rollback()
        尽力删除对象(storage_key)
        raise
    await db.refresh(asset)
    return 构建文娱资源读取(asset)


async def 从外部候选导入文娱(db: AsyncSession, user: 用户, body: 外部文娱导入请求) -> 文娱条目信息:
    """从外部候选导入文娱条目。"""
    detail = await 获取外部文娱详情(body.provider, body.external_id)
    item = 文娱条目(
        user_id=user.id,
        title=detail.title,
        original_title=detail.original_title,
        media_type=detail.media_type,
        status=body.status,
        rating=body.rating,
        creator="、".join(detail.creators) if detail.creators else None,
        summary=detail.summary,
        description=detail.description,
        genres=detail.genres,
        tags=detail.tags,
        personal_tags=[],
        release_date=detail.release_date,
        is_visible=body.is_visible,
    )
    db.add(item)
    await db.flush()
    db.add(
        文娱外部来源(
            media_item_id=item.id,
            provider=detail.provider,
            external_id=detail.external_id,
            external_url=detail.external_url,
            raw_data=detail.raw,
            fetched_at=utcnow(),
        )
    )
    await db.commit()

    if body.localize_cover and detail.cover_url:
        await 从外部URL导入封面(
            db,
            user,
            str(item.id),
            外部封面导入请求(
                external_url=detail.cover_url,
                source_provider=detail.provider,
                source_asset_id=detail.external_id,
                original_name=f"{detail.title}.jpg",
                set_primary=True,
            ),
        )

    return 构建文娱读取(await get_media_or_404(db, user, str(item.id)))


async def 创建外部封面引用(
    db: AsyncSession,
    user: 用户,
    media_id: str,
    body: 外部封面导入请求,
) -> 文娱资源信息:
    """仅保存外部封面引用，不下载本地化。"""
    item = await get_media_or_404(db, user, media_id)
    if body.set_primary:
        for asset in item.assets or []:
            if asset.asset_type == "cover":
                asset.is_primary = False
    asset = 文娱资源(
        user_id=user.id,
        media_item_id=item.id,
        asset_type="cover",
        external_url=body.external_url,
        thumbnail_url=body.external_url,
        source_provider=body.source_provider,
        source_asset_id=body.source_asset_id,
        original_name=body.original_name,
        attribution=body.attribution,
        license=body.license,
        is_primary=body.set_primary,
        imported_at=utcnow(),
    )
    db.add(asset)
    await db.flush()
    if body.set_primary:
        item.primary_cover_asset_id = asset.id
    await db.commit()
    await db.refresh(asset)
    return 构建文娱资源读取(asset)
