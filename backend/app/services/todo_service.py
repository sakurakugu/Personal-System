"""待办服务兼容入口。"""

from app.modules.todos.service import (
    _apply_completion,
    _calculate_next_reset_at,
    _get_deleted_todo_expire_at,
    _is_deleted_todo_expired,
    _refresh_todo_recurrence_state,
    complete_todo,
    create_todo,
    delete_todo,
    get_deleted_todo_or_404,
    get_todo_or_404,
    list_todo_tags,
    list_todos,
    restore_todo,
    toggle_pin,
    uncomplete_todo,
    update_todo,
)

__all__ = [
    "_apply_completion",
    "_calculate_next_reset_at",
    "_get_deleted_todo_expire_at",
    "_is_deleted_todo_expired",
    "_refresh_todo_recurrence_state",
    "complete_todo",
    "create_todo",
    "delete_todo",
    "get_deleted_todo_or_404",
    "get_todo_or_404",
    "list_todo_tags",
    "list_todos",
    "restore_todo",
    "toggle_pin",
    "uncomplete_todo",
    "update_todo",
]
