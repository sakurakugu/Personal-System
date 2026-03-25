"""重置待办事项表 - 全新结构

修订 ID: 001_reset_todos
创建时间: 2026-03-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision 标识符，由 Alembic 使用
revision: str = '001_reset_todos'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """删除旧表，创建新表结构。"""
    # 删除旧表（如果存在）
    op.execute('DROP TABLE IF EXISTS todos CASCADE')
    # 删除已存在的枚举类型
    op.execute("DROP TYPE IF EXISTS todostatus CASCADE")
    op.execute("DROP TYPE IF EXISTS recurrencetype CASCADE")
    
    # 创建新表
    op.create_table(
        'todos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('todo', 'in_progress', 'done', name='todostatus'), nullable=False),
        # 优先级双维度
        sa.Column('importance', sa.Integer(), nullable=False, server_default='33'),
        sa.Column('urgency', sa.Integer(), nullable=False, server_default='33'),
        # 时间范围
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        # 标记
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        # 软删除
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        # 标签（逗号分隔）
        sa.Column('tags', sa.Text(), nullable=True),
        # 循环设置（使用字符串存储类型）
        sa.Column('recurrence_type', sa.String(length=20), nullable=False, server_default='none'),
        sa.Column('recurrence_interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('recurrence_count', sa.Integer(), nullable=False, server_default='0'),
        # 时间戳
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        # 主键
        sa.PrimaryKeyConstraint('id'),
        # 外键
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # 创建索引
    op.create_index('ix_todos_user_id', 'todos', ['user_id'])
    op.create_index('ix_todos_status', 'todos', ['status'])
    op.create_index('ix_todos_is_deleted', 'todos', ['is_deleted'])
    op.create_index('ix_todos_is_pinned', 'todos', ['is_pinned'])


def downgrade() -> None:
    """回滚到旧表结构。"""
    op.drop_table('todos')
    
    # 创建旧表结构（简化版）
    op.create_table(
        'todos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('todo', 'in_progress', 'done', name='todostatus'), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
