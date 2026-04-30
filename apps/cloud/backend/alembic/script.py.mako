"""${message}

作者: sakurakugu
修订 ID: ${up_revision}
上一个修订: ${down_revision | comma,n}
创建时间: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision 标识符，由 Alembic 使用
revision: str = ${repr(up_revision)}                                    # 当前迁移的唯一标识
down_revision: Union[str, None] = ${repr(down_revision)}                # 上一个迁移的标识符，用于建立迁移链路（None 表示这是第一个迁移）
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)} # 分支标签，用于支持多分支迁移
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}       # 依赖的其他迁移，当前迁移依赖这些迁移先执行


def upgrade() -> None:
    """升级数据库结构。

    执行此迁移时将调用此函数，通常包含：
    - 创建新表 (op.create_table)
    - 添加新列 (op.add_column)
    - 创建索引 (op.create_index)
    - 修改列类型 (op.alter_column)
    - 删除表或列等操作
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """降级数据库结构。

    回滚此迁移时将调用此函数，应该执行与 upgrade 相反的操作：
    - 删除 upgrade 中创建的表
    - 删除 upgrade 中添加的列
    - 删除 upgrade 中创建的索引
    - 恢复 upgrade 中修改的列类型

    注意：某些操作（如删除列）可能导致数据丢失，请谨慎操作。
    """
    ${downgrades if downgrades else "pass"}
