"""规范化 AVIF 文件展示名称。

Revision ID: 20260408_00
Revises: 20260407_02
Create Date: 2026-04-08 16:10:00
"""

from __future__ import annotations

from pathlib import Path

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260408_00"
down_revision = "20260407_02"
branch_labels = None
depends_on = None


默认图片文件名 = "image"


def normalize_avif_name(original_name: str) -> str:
    """将展示名称统一为 .avif 后缀。"""
    normalized = original_name.strip()
    if not normalized:
        return f"{默认图片文件名}.avif"

    stem = Path(normalized).stem.strip()
    if not stem or stem == ".":
        stem = 默认图片文件名
    return f"{stem}.avif"


def backfill_table_original_names(table_name: str) -> None:
    """回填指定表中的 AVIF 展示名称。"""
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(f"SELECT id, original_name FROM {table_name} WHERE mime_type = 'image/avif'")
    ).mappings()
    update_sql = sa.text(f"UPDATE {table_name} SET original_name = :original_name WHERE id = :id")
    for row in rows:
        normalized_name = normalize_avif_name(str(row["original_name"]))
        if normalized_name == row["original_name"]:
            continue
        bind.execute(
            update_sql,
            {
                "id": row["id"],
                "original_name": normalized_name,
            },
        )


def upgrade() -> None:
    """升级迁移。"""
    backfill_table_original_names("files")
    backfill_table_original_names("article_images")


def downgrade() -> None:
    """回滚迁移。"""
    # 旧文件名无法可靠还原，此迁移不可逆。
    pass
