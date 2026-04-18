"""Bangumi 代理接口。

由于 Bangumi API 存在 CORS 限制，前端浏览器无法直接访问，
因此通过后端代理转发请求。
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query
from starlette.requests import Request

router = APIRouter(prefix="/bangumi", tags=["bangumi"])

BANGUMI_API_BASE = "https://api.bgm.tv"


@router.get("/collections")
async def proxy_bangumi_collections(
    request: Request,
    username: str = Query(..., description="Bangumi 用户名"),
    subject_type: int = Query(..., description="条目类型"),
    limit: int = Query(50, ge=1, le=50, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """代理获取 Bangumi 用户收藏列表。"""
    url = f"{BANGUMI_API_BASE}/v0/users/{username}/collections"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                url,
                params={
                    "subject_type": subject_type,
                    "limit": limit,
                    "offset": offset,
                },
                headers={
                    "Accept": "application/json",
                    "User-Agent": "web-system Blog",
                },
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"请求 Bangumi API 失败: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text or "Bangumi API 返回错误",
        )

    return response.json()
