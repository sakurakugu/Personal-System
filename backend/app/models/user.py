"""用户模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.common import utcnow
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.models.bill import BillAccount, BillCategory, BillRecord, BillTemplate
    from app.models.article import Article
    from app.models.comment import Comment, CommentLike
    from app.models.file import File
    from app.models.moment import Moment
    from app.models.todo import Todo


class UserRole(str, enum.Enum):
    """用户角色枚举。"""

    super_admin = "super_admin"
    admin = "admin"
    user = "user"


class User(Base):
    """用户模型。"""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    show_private_articles_on_home: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    articles: Mapped[list["Article"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="user")
    todos: Mapped[list["Todo"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_accounts: Mapped[list["BillAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_categories: Mapped[list["BillCategory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_records: Mapped[list["BillRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bill_templates: Mapped[list["BillTemplate"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    moments: Mapped[list["Moment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    liked_comments: Mapped[list["CommentLike"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
