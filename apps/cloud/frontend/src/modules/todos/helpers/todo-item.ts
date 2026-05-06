import { Clock, RefreshRight } from '@element-plus/icons-vue'
import {
  formatPreciseTodoDateTime,
  formatTodoDateTime,
  getTodoRecurrenceText,
  getTodoTrashExpireAt,
  getTodoTrashRemainingDeleteText,
  getTodoTrashRemainingDeleteDays,
  isTodoNearDeadline,
  isTodoOverdue,
  parseTodoTags,
  shouldKeepTodoAccentColor as shouldKeepSharedTodoAccentColor,
  sortTodosByStatusAndPinCreated as sortSharedTodosByStatusAndPinCreated,
  TODO_TRASH_RETENTION_DAYS,
  todoNextStatusLabel,
  todoRecurrenceOptions,
  todoStatusLabel,
  todoStatusOrder,
} from '@personal-system/modules/todos'
import { computed } from 'vue'
import { useThemeStore } from '../../../shared/stores/theme'
import type { Todo } from '../store'

export const 回收站保留天数 = TODO_TRASH_RETENTION_DAYS

// ============ 标签相关 ============

export function parseTags(tags: string[] | null): string[] {
  return parseTodoTags(tags)
}

// ============ 优先级相关 ============

export function getPriorityTagType(value: number): 'success' | 'info' | 'warning' | 'danger' {
  if (value >= 86) return 'danger'
  if (value >= 67) return 'warning'
  if (value >= 33) return 'success'
  return 'info'
}

export function getPriorityLabel(value: number): string {
  if (value >= 86) return '非常重要'
  if (value >= 67) return '重要'
  if (value >= 33) return '一般'
  return '不重要'
}

export function getPriorityAccentColor(value: number): string {
  if (value >= 86) return 'var(--el-color-danger)'
  if (value >= 67) return 'var(--el-color-warning)'
  if (value >= 33) return 'var(--el-color-success)'
  return 'var(--el-color-info)'
}

// ============ 日期相关 ============

export function isNearDeadline(endDate: string | null): boolean {
  return isTodoNearDeadline(endDate)
}

export function isOverdue(endDate: string | null): boolean {
  return isTodoOverdue(endDate)
}

export function formatDateTime(value: string | Date | null): string {
  return formatTodoDateTime(value)
}

export function formatPreciseDateTime(value: string | Date | null): string {
  return formatPreciseTodoDateTime(value)
}

export function getTrashExpireAt(deletedAt: string | Date | null): Date | null {
  return getTodoTrashExpireAt(deletedAt)
}

export function getTrashRemainingDeleteDays(deletedAt: string | Date | null): number | null {
  return getTodoTrashRemainingDeleteDays(deletedAt)
}

export function getTrashRemainingDeleteText(deletedAt: string | Date | null): string {
  return getTodoTrashRemainingDeleteText(deletedAt)
}

// ============ 循环相关 ============

export const recurrenceOptions = [
  ...todoRecurrenceOptions,
]

export function getRecurrenceText(type: string, interval?: number): string {
  return getTodoRecurrenceText(type, interval)
}

export function shouldKeepTodoAccentColor(todo: Todo): boolean {
  return shouldKeepSharedTodoAccentColor(todo)
}

// ============ 状态相关 ============

export const nextStatusLabel: Record<string, string> = {
  ...todoNextStatusLabel,
}

export const statusLabel: Record<string, string> = {
  ...todoStatusLabel,
}

export const statusOrder: Record<string, string> = {
  ...todoStatusOrder,
}

export const nextStatusIcon: Record<string, typeof RefreshRight> = {
  todo: RefreshRight,
  done: Clock,
}

// ============ 四象限相关 ============

export function getQuadrant(importance: number, urgency: number): number {
  if (importance >= 50 && urgency >= 50) return 1
  if (importance >= 50) return 2
  if (urgency >= 50) return 3
  return 4
}

export function sortTodosByStatusAndPinCreated(todos: Todo[]): Todo[] {
  return sortSharedTodosByStatusAndPinCreated(todos)
}

export function useSortedByQuadrant(todos: Todo[]) {
  return computed(() => {
    return sortTodosByStatusAndPinCreated(todos).sort((a, b) => {
      // 按象限排序
      const qa = getQuadrant(a.importance, a.urgency)
      const qb = getQuadrant(b.importance, b.urgency)
      return qa - qb
    })
  })
}

// ============ 进度样式相关 ============

export function useProgressStyle() {
  const themeStore = useThemeStore()

  function getProgressStyle(t: Todo) {
    if (t.recurrence_type === 'none' || t.times_per_interval <= 1) {
      return {}
    }
    const total = Math.max(1, t.times_per_interval)
    const done = Math.min(t.interval_progress || 0, total)
    if (done <= 0) {
      return {}
    }
    const pct = Math.floor((done / total) * 100)
    const progressColor = themeStore.isDark ? 'rgba(103, 194, 58, 0.25)' : 'rgba(103, 194, 58, 0.15)'
    return {
      backgroundImage: `linear-gradient(to right, ${progressColor} ${pct}%, transparent ${pct}%)`,
      backgroundRepeat: 'no-repeat',
    }
  }

  return { getProgressStyle }
}
