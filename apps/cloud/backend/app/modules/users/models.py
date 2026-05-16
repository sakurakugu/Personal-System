"""用户模块相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.shared.db.session import Base
from app.utils.email import 构建邮箱身份
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.articles.models import 文章
    from app.modules.bills.models import BillAccount, BillCategory, BillRecord, BillTemplate
    from app.modules.collections.models import 收藏
    from app.modules.files.models import File, FileFolder
    from app.modules.moments.models import 动态
    from app.modules.todos.models import Todo


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class 用户角色(str, enum.Enum):
    """用户角色枚举。"""

    super_admin = "super_admin"
    admin = "admin"
    user = "user"


class 用户设置(Base):
    """用户设置模型。"""

    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    show_private_articles_on_home: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["用户"] = relationship(back_populates="settings")


def 构建默认用户设置() -> 用户设置:
    """构造默认用户设置。"""
    return 用户设置(show_private_articles_on_home=False)


class 用户(Base):
    """用户模型。"""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_identity: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[用户角色] = mapped_column(Enum(用户角色, name="userrole"), default=用户角色.user, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    articles: Mapped[list["文章"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    collections: Mapped[list["收藏"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    todos: Mapped[list["Todo"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_accounts: Mapped[list["BillAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_categories: Mapped[list["BillCategory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_records: Mapped[list["BillRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_templates: Mapped[list["BillTemplate"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    file_folders: Mapped[list["FileFolder"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    moments: Mapped[list["动态"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    settings: Mapped["用户设置 | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="joined",
        single_parent=True,
    )

    @validates("email")
    def sync_email_identity(self, _key: str, value: str) -> str:
        """同步邮箱判重键。"""
        self.email_identity = 构建邮箱身份(value)
        return value

    def ensure_settings(self) -> "用户设置":
        """确保当前用户拥有设置对象。"""
        if self.settings is None:
            self.settings = 构建默认用户设置()
        return self.settings
