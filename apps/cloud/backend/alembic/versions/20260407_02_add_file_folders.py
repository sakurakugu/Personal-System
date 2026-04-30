"""新增文件夹模型并为普通文件增加目录归属。

Revision ID: 20260407_02
Revises: 20260407_01
Create Date: 2026-04-07 23:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260407_02"
down_revision = "20260407_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "file_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["file_folders.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_file_folders_user_id_parent_id_created_at",
        "file_folders",
        ["user_id", "parent_id", "created_at"],
        unique=False,
    )

    op.add_column("files", sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_files_folder_id_file_folders",
        "files",
        "file_folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_index("ix_files_user_id_purpose_created_at", table_name="files")
    op.create_index(
        "ix_files_user_id_purpose_folder_id_created_at",
        "files",
        ["user_id", "purpose", "folder_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_files_user_id_purpose_folder_id_created_at", table_name="files")
    op.create_index(
        "ix_files_user_id_purpose_created_at",
        "files",
        ["user_id", "purpose", "created_at"],
        unique=False,
    )

    op.drop_constraint("fk_files_folder_id_file_folders", "files", type_="foreignkey")
    op.drop_column("files", "folder_id")

    op.drop_index("ix_file_folders_user_id_parent_id_created_at", table_name="file_folders")
    op.drop_table("file_folders")
