"""将文娱评分范围扩展到 15 级。"""

from __future__ import annotations

from alembic import op


revision = "20260526_01"
down_revision = "20260526_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.drop_constraint("ck_media_items_rating_range", "media_items", type_="check")
    op.create_check_constraint(
        "ck_media_items_rating_range",
        "media_items",
        "rating IS NULL OR (rating >= 1 AND rating <= 15)",
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_constraint("ck_media_items_rating_range", "media_items", type_="check")
    op.create_check_constraint(
        "ck_media_items_rating_range",
        "media_items",
        "rating IS NULL OR (rating >= 1 AND rating <= 10)",
    )
