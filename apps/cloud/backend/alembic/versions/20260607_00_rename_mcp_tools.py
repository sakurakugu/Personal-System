"""统一 MCP 工具命名。

Revision ID: 20260607_00
Revises: 20260606_04
Create Date: 2026-06-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260607_00"
down_revision = "20260606_04"
branch_labels = None
depends_on = None


工具名映射 = {
    "articles.list_mine": "articles.list",
    "articles.get_summary": "articles.summary.get",
    "articles.get_outline": "articles.outline.get",
    "articles.get_content": "articles.content.get",
    "articles.update_metadata": "articles.metadata.update",
    "articles.replace_content": "articles.content.replace",
    "articles.patch_content": "articles.content.patch",
    "moments.list_mine": "moments.list",
    "operations.list_recent": "operations.list",
    "stats.blog_overview": "stats.blog.overview",
    "stats.content_overview": "stats.content.overview",
    "stats.activity_trend": "stats.activity.trend",
    "media.facets": "media.facets.get",
    "media.update_metadata": "media.metadata.update",
    "files.explorer": "files.list",
    "files.get_metadata": "files.metadata.get",
    "files.trash_list": "files.trash.list",
    "files.folder_create": "files.folder.create",
    "files.folder_rename": "files.folder.rename",
    "files.folder_move": "files.folder.move",
    "files.folder_delete": "files.folder.delete",
    "files.folder_restore": "files.folder.restore",
    "files.rename": "files.file.rename",
    "files.move": "files.file.move",
    "files.delete": "files.file.delete",
    "files.restore": "files.file.restore",
}


def _更新工具名(mapping: dict[str, str]) -> None:
    """更新操作日志中的工具名称。"""
    bind = op.get_bind()
    statement = sa.text(
        """
        UPDATE mcp_operation_logs
        SET
            tool_name = CASE WHEN tool_name = :old_name THEN :new_name ELSE tool_name END,
            undo_tool_name = CASE WHEN undo_tool_name = :old_name THEN :new_name ELSE undo_tool_name END,
            result_json = CASE
                WHEN result_json ->> 'undo_tool_name' = :old_name
                THEN jsonb_set(result_json, '{undo_tool_name}', to_jsonb(CAST(:new_name AS text)), false)
                ELSE result_json
            END
        WHERE
            tool_name = :old_name
            OR undo_tool_name = :old_name
            OR result_json ->> 'undo_tool_name' = :old_name
        """
    )
    for old_name, new_name in mapping.items():
        bind.execute(statement, {"old_name": old_name, "new_name": new_name})


def upgrade() -> None:
    """升级数据库数据。"""
    _更新工具名(工具名映射)


def downgrade() -> None:
    """回滚数据库数据。"""
    _更新工具名({new_name: old_name for old_name, new_name in 工具名映射.items()})
