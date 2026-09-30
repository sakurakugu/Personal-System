"""将备忘录数据并入文章并移除独立备忘录表。"""

from __future__ import annotations

import logging
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20261001_01"
down_revision = "20261001_00"
branch_labels = None
depends_on = None
logger = logging.getLogger(__name__)


def upgrade() -> None:
    """迁移旧内容并清理备忘录结构。"""
    bind = op.get_bind()
    op.add_column("articles", sa.Column("import_metadata", postgresql.JSONB(), nullable=True))

    memos = bind.execute(sa.text("""
        SELECT id, user_id, content, status::text AS status, source::text AS source,
               converted_to_type, converted_to_id, archived_at, deleted_at, created_at, updated_at
        FROM memos ORDER BY created_at, id
    """)).mappings().all()

    if memos:
        tag_name = "原备忘录"
        tag_id = bind.execute(sa.text("SELECT id FROM tags WHERE name = :name"), {"name": tag_name}).scalar_one_or_none()
        if tag_id is None:
            tag_id = uuid4()
            bind.execute(sa.text("""
                INSERT INTO tags (id, name, slug, created_at)
                VALUES (:id, :name, :slug, now())
            """), {"id": tag_id, "name": tag_name, "slug": f"imported-memo-{tag_id}"})

        for memo in memos:
            content = memo["content"]
            title = next((line.strip() for line in content.splitlines() if line.strip()), "未命名文章")[:300]
            metadata = {
                "kind": "memo",
                "status": memo["status"],
                "source": memo["source"],
                "archived_at": memo["archived_at"].isoformat() if memo["archived_at"] else None,
                "converted_to_type": memo["converted_to_type"],
                "converted_to_id": str(memo["converted_to_id"]) if memo["converted_to_id"] else None,
            }
            bind.execute(sa.text("""
                INSERT INTO articles
                    (id, title, slug, content, import_metadata, revision, word_count, author_id,
                     is_deleted, deleted_at, created_at, last_edited_at, updated_at)
                VALUES
                    (:id, :title, :slug, :content, :metadata, 1, :word_count, :author_id,
                     :is_deleted, :deleted_at, :created_at, :updated_at, :updated_at)
            """).bindparams(sa.bindparam("metadata", type_=postgresql.JSONB())), {
                "id": memo["id"],
                "title": title,
                "slug": f"memo-{memo['id']}",
                "content": content,
                "metadata": metadata,
                "word_count": len(content),
                "author_id": memo["user_id"],
                "is_deleted": memo["deleted_at"] is not None,
                "deleted_at": memo["deleted_at"],
                "created_at": memo["created_at"],
                "updated_at": memo["updated_at"],
            })
            bind.execute(sa.text("""
                INSERT INTO article_tags (article_id, tag_id) VALUES (:article_id, :tag_id)
            """), {"article_id": memo["id"], "tag_id": tag_id})

    op.drop_table("memos")
    postgresql.ENUM(name="memosource").drop(bind, checkfirst=True)
    postgresql.ENUM(name="memostatus").drop(bind, checkfirst=True)
    logger.info("备忘录并入文章完成，迁移数量=%s", len(memos))


def downgrade() -> None:
    """还原迁入的备忘录及原有文章。"""
    bind = op.get_bind()
    status_enum = postgresql.ENUM("inbox", "processed", "archived", "dropped", name="memostatus", create_type=False)
    source_enum = postgresql.ENUM("manual", "wechat", "web", "share", "unknown", name="memosource", create_type=False)
    status_enum.create(bind, checkfirst=True)
    source_enum.create(bind, checkfirst=True)
    op.create_table(
        "memos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("source", source_enum, nullable=False),
        sa.Column("converted_to_type", sa.String(50)),
        sa.Column("converted_to_id", postgresql.UUID(as_uuid=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("(status = 'archived' AND archived_at IS NOT NULL) OR (status <> 'archived' AND archived_at IS NULL)", name="ck_memos_archived_state"),
        sa.CheckConstraint("(deleted_at IS NULL AND status <> 'dropped') OR deleted_at IS NOT NULL", name="ck_memos_deleted_state"),
        sa.CheckConstraint("(converted_to_type IS NULL AND converted_to_id IS NULL) OR (converted_to_type IS NOT NULL AND converted_to_id IS NOT NULL)", name="ck_memos_converted_target"),
    )
    op.create_index("ix_memos_user_id_deleted_at_status_updated_at", "memos", ["user_id", "deleted_at", "status", "updated_at"])
    op.create_index("ix_memos_user_id_converted_to_type", "memos", ["user_id", "converted_to_type"])
    bind.execute(sa.text("""
        INSERT INTO memos
            (id, user_id, content, status, source, converted_to_type, converted_to_id,
             archived_at, deleted_at, created_at, updated_at)
        SELECT id, author_id, content,
               (import_metadata->>'status')::memostatus,
               (import_metadata->>'source')::memosource,
               import_metadata->>'converted_to_type',
               (import_metadata->>'converted_to_id')::uuid,
               (import_metadata->>'archived_at')::timestamptz,
               deleted_at, created_at, updated_at
        FROM articles WHERE import_metadata->>'kind' = 'memo'
    """))
    bind.execute(sa.text("DELETE FROM articles WHERE import_metadata->>'kind' = 'memo'"))
    op.drop_column("articles", "import_metadata")
