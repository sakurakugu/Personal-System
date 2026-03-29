"""待办循环逻辑单测。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.models.todo import RecurrenceType, Todo, TodoStatus
from app.services.todo_service import (
    _apply_completion,
    _calculate_next_reset_at,
    _get_deleted_todo_expire_at,
    _is_deleted_todo_expired,
    _refresh_todo_recurrence_state,
)
from app.utils.uuid import generate_uuid7


LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc


def local_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造本地时区时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=LOCAL_TZ)


def utc_from_local(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """将本地时区时间转换为 UTC。"""
    return local_dt(year, month, day, hour, minute).astimezone(timezone.utc)


def build_todo(**overrides: object) -> Todo:
    """构造测试用待办。"""
    defaults: dict[str, object] = {
        "user_id": generate_uuid7(),
        "title": "测试待办",
        "status": TodoStatus.todo,
        "importance": 33,
        "urgency": 33,
        "is_pinned": False,
        "is_deleted": False,
        "recurrence_type": RecurrenceType.daily,
        "recurrence_interval": 1,
        "recurrence_count": -1,
        "times_per_interval": 1,
        "interval_progress": 0,
        "progress_reset_at": None,
        "created_at": utc_from_local(2026, 3, 28, 9, 0),
        "updated_at": utc_from_local(2026, 3, 28, 9, 0),
    }
    defaults.update(overrides)
    return Todo(**defaults)


class TodoRecurrenceServiceTest(unittest.TestCase):
    """循环待办状态计算测试。"""

    def test_读取时会把跨天已完成的每日任务恢复为待办(self) -> None:
        todo = build_todo(
            status=TodoStatus.done,
            updated_at=utc_from_local(2026, 3, 28, 20, 0),
        )

        changed = _refresh_todo_recurrence_state(
            todo,
            now=utc_from_local(2026, 3, 29, 8, 0),
        )

        self.assertTrue(changed)
        self.assertEqual(todo.status, TodoStatus.todo)
        self.assertEqual(todo.interval_progress, 0)
        self.assertIsNone(todo.progress_reset_at)

    def test_工作日任务完成后会跳过周末安排到下个工作日(self) -> None:
        todo = build_todo(
            recurrence_type=RecurrenceType.workday,
            updated_at=utc_from_local(2026, 10, 9, 18, 0),
        )

        _apply_completion(todo, completed_at=utc_from_local(2026, 10, 9, 18, 0))

        self.assertEqual(todo.status, TodoStatus.done)
        self.assertEqual(
            todo.progress_reset_at,
            utc_from_local(2026, 10, 10, 0, 0),
        )

    def test_节假日任务完成后会安排到下一个法定节假日(self) -> None:
        todo = build_todo(
            recurrence_type=RecurrenceType.holiday,
            updated_at=utc_from_local(2026, 9, 30, 18, 0),
        )

        _apply_completion(todo, completed_at=utc_from_local(2026, 9, 30, 18, 0))

        self.assertEqual(todo.status, TodoStatus.done)
        self.assertEqual(
            todo.progress_reset_at,
            utc_from_local(2026, 10, 1, 0, 0),
        )

    def test_有限循环次数耗尽后不再安排下一次重置(self) -> None:
        todo = build_todo(
            recurrence_count=1,
            updated_at=utc_from_local(2026, 3, 28, 10, 0),
        )

        _apply_completion(todo, completed_at=utc_from_local(2026, 3, 28, 10, 0))

        self.assertEqual(todo.status, TodoStatus.done)
        self.assertEqual(todo.recurrence_count, 0)
        self.assertIsNone(todo.progress_reset_at)

    def test_每月三十一号会跳过不存在该日期的月份(self) -> None:
        todo = build_todo(
            recurrence_type=RecurrenceType.monthly,
            start_date=utc_from_local(2026, 1, 31, 9, 0),
            created_at=utc_from_local(2026, 1, 31, 9, 0),
            updated_at=utc_from_local(2026, 1, 31, 18, 0),
        )

        next_reset_at = _calculate_next_reset_at(
            todo,
            reference_at=utc_from_local(2026, 1, 31, 18, 0),
        )

        self.assertEqual(next_reset_at, utc_from_local(2026, 3, 31, 0, 0))

    def test_跨天后会清空未完成的周期进度(self) -> None:
        todo = build_todo(
            times_per_interval=3,
            interval_progress=2,
            progress_reset_at=utc_from_local(2026, 3, 29, 0, 0),
            updated_at=utc_from_local(2026, 3, 28, 21, 0),
        )

        changed = _refresh_todo_recurrence_state(
            todo,
            now=utc_from_local(2026, 3, 29, 9, 0),
        )

        self.assertTrue(changed)
        self.assertEqual(todo.status, TodoStatus.todo)
        self.assertEqual(todo.interval_progress, 0)
        self.assertIsNone(todo.progress_reset_at)

    def test_回收站待办会在删除九十天后过期(self) -> None:
        deleted_at = utc_from_local(2026, 1, 1, 9, 30)

        self.assertEqual(
            _get_deleted_todo_expire_at(deleted_at),
            utc_from_local(2026, 4, 1, 9, 30),
        )
        self.assertFalse(
            _is_deleted_todo_expired(
                deleted_at,
                now=utc_from_local(2026, 4, 1, 9, 29),
            )
        )
        self.assertTrue(
            _is_deleted_todo_expired(
                deleted_at,
                now=utc_from_local(2026, 4, 1, 9, 30),
            )
        )


if __name__ == "__main__":
    unittest.main()
