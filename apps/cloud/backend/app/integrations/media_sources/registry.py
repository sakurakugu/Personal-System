"""文娱外部数据源注册表。"""

from __future__ import annotations

import httpx

from app.integrations.media_sources.anilist import AniList数据源
from app.integrations.media_sources.bangumi import Bangumi数据源
from app.integrations.media_sources.base import 外部文娱数据源
from app.integrations.media_sources.google_books import GoogleBooks数据源
from app.integrations.media_sources.igdb import IGDB数据源
from app.integrations.media_sources.open_library import OpenLibrary数据源
from app.integrations.media_sources.rawg import RAWG数据源
from app.integrations.media_sources.tmdb import TMDB数据源
from app.integrations.media_sources.vndb import VNDB数据源

数据源类型 = [
    Bangumi数据源,
    AniList数据源,
    GoogleBooks数据源,
    OpenLibrary数据源,
    VNDB数据源,
    TMDB数据源,
    RAWG数据源,
    IGDB数据源,
]


def 获取外部文娱数据源列表(client: httpx.AsyncClient) -> list[外部文娱数据源]:
    """获取全部已注册外部文娱数据源。"""
    return [source_type(client) for source_type in 数据源类型]


def 获取外部文娱数据源(client: httpx.AsyncClient, provider: str) -> 外部文娱数据源 | None:
    """按 provider 获取外部文娱数据源。"""
    normalized_provider = provider.strip().lower()
    for source in 获取外部文娱数据源列表(client):
        if source.provider == normalized_provider:
            return source
    return None
