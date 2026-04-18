"""公告 Schema 兼容入口。"""

from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementPublicRead, AnnouncementRead, AnnouncementUpdate

__all__ = [
    "AnnouncementCreate",
    "AnnouncementPublicRead",
    "AnnouncementRead",
    "AnnouncementUpdate",
]
