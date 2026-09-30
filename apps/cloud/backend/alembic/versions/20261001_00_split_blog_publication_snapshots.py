"""拆分文章和博客发布快照，迁移现有链接及互动统计。"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261001_00"
down_revision = "20260925_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.create_table(
        "blog_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(350), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.String(500)),
        sa.Column("cover_url", sa.String(500)),
        sa.Column("category_snapshot", postgresql.JSONB()),
        sa.Column("tags_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("source_revision", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_edited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('public', 'login_required')", name="ck_blog_visibility"),
    )
    op.create_index("ix_blog_published_at", "blog_publications", ["is_published", "published_at"])
    op.execute("""
        INSERT INTO blog_publications
        (id, author_id, slug, title, content, excerpt, cover_url, category_snapshot,
         tags_snapshot, status, is_published, source_revision, version, word_count,
         view_count, like_count, published_at, created_at, last_edited_at, updated_at)
        SELECT a.id, a.author_id, a.slug, a.title, a.content, a.excerpt, a.cover_url,
               CASE WHEN c.id IS NULL THEN NULL ELSE to_jsonb(c) END,
               COALESCE((SELECT jsonb_agg(to_jsonb(t) ORDER BY t.id)
                         FROM article_tags at JOIN tags t ON t.id = at.tag_id
                         WHERE at.article_id = a.id), '[]'::jsonb),
               a.status::text, NOT a.is_deleted, 1, 1, a.word_count,
               a.view_count, a.like_count, a.published_at, a.created_at, a.last_edited_at, a.updated_at
        FROM articles a LEFT JOIN categories c ON c.id = a.category_id
        WHERE a.status IN ('public', 'login_required')
    """)
    op.execute("""
        DELETE FROM feed_items WHERE type = 'article'
        AND source_id NOT IN (SELECT id FROM blog_publications WHERE is_published)
    """)
    op.drop_constraint("ck_articles_status_published_at", "articles", type_="check")
    op.drop_index("ix_articles_status_published_at", table_name="articles")
    for name in ("status", "published_at", "view_count", "like_count"):
        op.drop_column("articles", name)
    op.alter_column("articles", "revision", server_default=None)


def downgrade() -> None:
    status_type = postgresql.ENUM("private", "login_required", "public", name="articlestatus", create_type=False)
    op.add_column("articles", sa.Column("status", status_type, nullable=False, server_default="private"))
    op.add_column("articles", sa.Column("published_at", sa.DateTime(timezone=True)))
    op.add_column("articles", sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("articles", sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"))
    op.execute("""
        UPDATE articles a SET status = CASE WHEN b.is_published THEN b.status::articlestatus ELSE 'private'::articlestatus END,
            published_at = CASE WHEN b.is_published THEN b.published_at ELSE NULL END,
            view_count = b.view_count, like_count = b.like_count
        FROM blog_publications b WHERE b.id = a.id
    """)
    op.create_check_constraint("ck_articles_status_published_at", "articles",
        "(status = 'private' AND published_at IS NULL) OR (status IN ('login_required', 'public') AND published_at IS NOT NULL)")
    op.create_index("ix_articles_status_published_at", "articles", ["status", "published_at"])
    op.drop_table("blog_publications")
    op.drop_column("articles", "revision")
