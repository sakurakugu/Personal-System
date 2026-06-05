"""为文件和文件夹新增回收站字段。

Revision ID: 20260606_02
Revises: 20260606_01
Create Date: 2026-06-06 02:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260606_02"
down_revision = "20260606_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column("files", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("files", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("files", sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("files", sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True))
    op.add_column("files", sa.Column("purged_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_files_deleted_by_users", "files", "users", ["deleted_by"], ["id"], ondelete="SET NULL")
    op.alter_column("files", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_files_deleted_state",
        "files",
        "(is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL AND purge_after IS NULL AND purged_at IS NULL) "
        "OR (is_deleted = TRUE AND deleted_at IS NOT NULL AND purge_after IS NOT NULL)",
    )
    op.create_index(
        "ix_files_user_id_is_deleted_purpose_folder_id_created_at",
        "files",
        ["user_id", "is_deleted", "purpose", "folder_id", "created_at"],
    )
    op.create_index("ix_files_is_deleted_purge_after", "files", ["is_deleted", "purge_after"])

    op.add_column("file_folders", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("file_folders", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("file_folders", sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("file_folders", sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_file_folders_deleted_by_users",
        "file_folders",
        "users",
        ["deleted_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("file_folders", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_file_folders_deleted_state",
        "file_folders",
        "(is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL AND purge_after IS NULL) "
        "OR (is_deleted = TRUE AND deleted_at IS NOT NULL AND purge_after IS NOT NULL)",
    )
    op.create_index(
        "ix_file_folders_user_id_is_deleted_parent_id_created_at",
        "file_folders",
        ["user_id", "is_deleted", "parent_id", "created_at"],
    )
    op.create_index("ix_file_folders_is_deleted_purge_after", "file_folders", ["is_deleted", "purge_after"])


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_file_folders_is_deleted_purge_after", table_name="file_folders")
    op.drop_index("ix_file_folders_user_id_is_deleted_parent_id_created_at", table_name="file_folders")
    op.drop_constraint("ck_file_folders_deleted_state", "file_folders", type_="check")
    op.drop_constraint("fk_file_folders_deleted_by_users", "file_folders", type_="foreignkey")
    op.drop_column("file_folders", "purge_after")
    op.drop_column("file_folders", "deleted_by")
    op.drop_column("file_folders", "deleted_at")
    op.drop_column("file_folders", "is_deleted")

    op.drop_index("ix_files_is_deleted_purge_after", table_name="files")
    op.drop_index("ix_files_user_id_is_deleted_purpose_folder_id_created_at", table_name="files")
    op.drop_constraint("ck_files_deleted_state", "files", type_="check")
    op.drop_constraint("fk_files_deleted_by_users", "files", type_="foreignkey")
    op.drop_column("files", "purged_at")
    op.drop_column("files", "purge_after")
    op.drop_column("files", "deleted_by")
    op.drop_column("files", "deleted_at")
    op.drop_column("files", "is_deleted")
