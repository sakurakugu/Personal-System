"""将 Feed 条目主键统一迁移为 UUIDv7。

Revision ID: 20260329_01
Revises: 20260329_00
Create Date: 2026-03-29 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.utils.uuid import generate_uuid7


# revision identifiers, used by Alembic.
revision = "20260329_01"
down_revision = "20260329_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """将现有 feed_items 主键改写为 UUIDv7。"""
    bind = op.get_bind()
    feed_items = sa.table(
        "feed_items",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )

    rows = bind.execute(
        sa.select(feed_items.c.id).order_by(feed_items.c.published_at.asc(), feed_items.c.id.asc())
    ).mappings()

    for row in rows:
        bind.execute(
            sa.update(feed_items)
            .where(feed_items.c.id == row["id"])
            .values(id=generate_uuid7())
        )


def downgrade() -> None:
    """此迁移不可逆。"""
    raise RuntimeError("feed_items 主键改写为 UUIDv7 后无法无损回滚")
