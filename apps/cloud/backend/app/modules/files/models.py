"""文件模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.users.models import 用户


class FilePurpose(str, enum.Enum):
    """文件用途枚举。"""

    file = "file"
    article_image = "article_image"
    moment_image = "moment_image"


class FileFolder(Base):
    """文件夹模型。"""

    __tablename__ = "file_folders"
    __table_args__ = (
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL AND purge_after IS NULL) "
            "OR (is_deleted = TRUE AND deleted_at IS NOT NULL AND purge_after IS NOT NULL)",
            name="ck_file_folders_deleted_state",
        ),
        Index("ix_file_folders_user_id_parent_id_created_at", "user_id", "parent_id", "created_at"),
        Index("ix_file_folders_user_id_is_deleted_parent_id_created_at", "user_id", "is_deleted", "parent_id", "created_at"),
        Index("ix_file_folders_is_deleted_purge_after", "is_deleted", "purge_after"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("file_folders.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    purge_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["用户"] = relationship(back_populates="file_folders", foreign_keys=[user_id])
    parent: Mapped["FileFolder | None"] = relationship(
        back_populates="children",
        remote_side="FileFolder.id",
    )
    children: Mapped[list["FileFolder"]] = relationship(back_populates="parent")
    files: Mapped[list["File"]] = relationship(back_populates="folder")


class File(Base):
    """上传文件模型。"""

    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL AND purge_after IS NULL AND purged_at IS NULL) "
            "OR (is_deleted = TRUE AND deleted_at IS NOT NULL AND purge_after IS NOT NULL)",
            name="ck_files_deleted_state",
        ),
        Index("ix_files_user_id_purpose_folder_id_created_at", "user_id", "purpose", "folder_id", "created_at"),
        Index(
            "ix_files_user_id_is_deleted_purpose_folder_id_created_at",
            "user_id",
            "is_deleted",
            "purpose",
            "folder_id",
            "created_at",
        ),
        Index("ix_files_is_deleted_purge_after", "is_deleted", "purge_after"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    folder_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("file_folders.id", ondelete="SET NULL"),
    )
    purpose: Mapped[FilePurpose] = mapped_column(
        Enum(FilePurpose, name="filepurpose"),
        default=FilePurpose.file,
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    purge_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped["用户"] = relationship(back_populates="files", foreign_keys=[user_id])
    folder: Mapped["FileFolder | None"] = relationship(back_populates="files")
