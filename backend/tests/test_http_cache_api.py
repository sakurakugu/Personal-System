"""公开只读接口条件缓存测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.api.v1.admin import get_public_settings
from app.api.v1.announcements import get_latest_announcement, get_public_announcements
from app.api.v1.calendar import get_holiday_calendar_year
from app.api.v1.categories_tags import list_categories
from app.api.v1.links import list_public_links
from app.models.announcement import Announcement
from app.models.article import Category
from app.models.user import User, UserRole
from app.schemas.link import LinkPublicRead
from app.schemas.system import SystemSettingsRead


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_user() -> User:
    """构造测试用户。"""
    return User(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=UserRole.user,
    )


def build_scalars_all_result(records: list[object]) -> SimpleNamespace:
    """构造支持 scalars().all() 的查询结果桩。"""
    return SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: records),
    )


def build_scalar_one_or_none_result(record: object | None) -> SimpleNamespace:
    """构造支持 scalar_one_or_none 的查询结果桩。"""
    return SimpleNamespace(scalar_one_or_none=lambda: record)


def build_scalar_one_result(record: object | None) -> SimpleNamespace:
    """构造支持 scalar_one 的查询结果桩。"""
    return SimpleNamespace(scalar_one=lambda: record)


class PublicJsonCacheApiTest(unittest.IsolatedAsyncioTestCase):
    """公开只读接口条件缓存测试。"""

    @patch("app.api.v1.admin.read_system_settings_with_updated_at")
    async def test_公开设置支持_etag_条件缓存(self, read_system_settings_with_updated_at) -> None:
        payload = SystemSettingsRead(
            comments_enabled=True,
            comments_stealth=False,
            comments_min_role="guest",
            register_enabled=True,
        )
        read_system_settings_with_updated_at.return_value = (payload, utc_dt(2026, 4, 9, 10, 0))

        response = await get_public_settings(db=AsyncMock())

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)
        self.assertIn("last-modified", response.headers)

        cached_response = await get_public_settings(
            if_none_match=response.headers["etag"],
            db=AsyncMock(),
        )

        self.assertEqual(cached_response.status_code, 304)

    async def test_公告列表支持_etag_条件缓存(self) -> None:
        announcement = Announcement(
            id=uuid4(),
            title="维护通知",
            content="今晚维护",
            is_active=True,
            created_by=uuid4(),
            created_at=utc_dt(2026, 4, 9, 9, 0),
            updated_at=utc_dt(2026, 4, 9, 9, 30),
        )
        db = AsyncMock()
        db.execute.return_value = build_scalars_all_result([announcement])

        response = await get_public_announcements(db=db)

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)

        cached_response = await get_public_announcements(
            if_none_match=response.headers["etag"],
            db=db,
        )

        self.assertEqual(cached_response.status_code, 304)

    async def test_最新公告支持_last_modified_条件缓存(self) -> None:
        announcement = Announcement(
            id=uuid4(),
            title="维护通知",
            content="今晚维护",
            is_active=True,
            created_by=uuid4(),
            created_at=utc_dt(2026, 4, 9, 9, 0),
            updated_at=utc_dt(2026, 4, 9, 9, 30),
        )
        db = AsyncMock()
        db.execute.return_value = build_scalar_one_or_none_result(announcement)

        response = await get_latest_announcement(db=db)

        self.assertEqual(response.status_code, 200)
        self.assertIn("last-modified", response.headers)

        cached_response = await get_latest_announcement(
            if_modified_since=response.headers["last-modified"],
            db=db,
        )

        self.assertEqual(cached_response.status_code, 304)

    @patch("app.api.v1.links.list_public_links_service")
    async def test_公开友链支持_etag_条件缓存(self, list_public_links_service) -> None:
        link = LinkPublicRead(
            id=uuid4(),
            name="示例站点",
            url="https://example.com",
            description="desc",
            logo_url=None,
        )
        list_public_links_service.return_value = [link]
        db = AsyncMock()
        db.execute.return_value = build_scalar_one_result(utc_dt(2026, 4, 9, 8, 0))

        response = await list_public_links(db=db)

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)

        cached_response = await list_public_links(
            if_none_match=response.headers["etag"],
            db=db,
        )

        self.assertEqual(cached_response.status_code, 304)

    async def test_分类列表支持_etag_条件缓存(self) -> None:
        category = Category(
            id=uuid4(),
            name="技术",
            slug="tech",
            description="desc",
            created_at=utc_dt(2026, 4, 9, 7, 0),
        )
        db = AsyncMock()
        db.execute.return_value = build_scalars_all_result([category])

        response = await list_categories(db=db)

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)

        cached_response = await list_categories(
            if_none_match=response.headers["etag"],
            db=db,
        )

        self.assertEqual(cached_response.status_code, 304)

    async def test_节假日日历支持_etag_条件缓存(self) -> None:
        user = build_user()

        response = await get_holiday_calendar_year(2026, _user=user)

        self.assertEqual(response.status_code, 200)
        self.assertIn("etag", response.headers)

        cached_response = await get_holiday_calendar_year(
            2026,
            if_none_match=response.headers["etag"],
            _user=user,
        )

        self.assertEqual(cached_response.status_code, 304)


if __name__ == "__main__":
    unittest.main()
