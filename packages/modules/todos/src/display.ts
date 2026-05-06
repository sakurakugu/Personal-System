import type { RecurrenceType, Todo, TodoStatus } from '@personal-system/domain/todos'

const DAY_IN_MS = 24 * 60 * 60 * 1000

export const TODO_TRASH_RETENTION_DAYS = 90

export const todoRecurrenceOptions: ReadonlyArray<{
  label: string
  value: RecurrenceType
}> = [
  { label: '不循环', value: 'none' },
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' },
  { label: '每年', value: 'yearly' },
  { label: '工作日（含调休）', value: 'workday' },
  { label: '周末（周六、周日）', value: 'weekend' },
  { label: '节假日(含周末）', value: 'holiday' },
  { label: '自定义', value: 'custom' },
] as const

export const todoStatusLabel: Record<TodoStatus, string> = {
  todo: '待办',
  done: '已完成',
}

export const todoNextStatusLabel: Record<TodoStatus, string> = {
  todo: '设为完成',
  done: '重设为待办',
}

export const todoStatusOrder: Record<TodoStatus, TodoStatus> = {
  todo: 'done',
  done: 'todo',
}

function parseDateInput(value: string | Date | null): Date | null {
  if (!value) {
    return null
  }

  const date = value instanceof Date ? new Date(value.getTime()) : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function padNumber(value: number): string {
  return String(value).padStart(2, '0')
}

export function parseTodoTags(tags: string[] | null): string[] {
  if (!tags) {
    return []
  }
  return tags.map(tag => tag.trim()).filter(Boolean)
}

export function isTodoNearDeadline(endDate: string | null): boolean {
  const end = parseDateInput(endDate)
  if (!end) {
    return false
  }

  const diff = end.getTime() - Date.now()
  return diff > 0 && diff < DAY_IN_MS
}

export function isTodoOverdue(endDate: string | null): boolean {
  const end = parseDateInput(endDate)
  if (!end) {
    return false
  }
  return end.getTime() < Date.now()
}

export function formatTodoDateTime(
  value: string | Date | null,
  options?: {
    emptyText?: string
    invalidText?: string
  },
): string {
  if (!value) {
    return options?.emptyText ?? ''
  }

  const date = parseDateInput(value)
  if (!date) {
    return options?.invalidText ?? ''
  }

  return `${date.getMonth() + 1}/${date.getDate()} ${padNumber(date.getHours())}:${padNumber(date.getMinutes())}`
}

export function formatPreciseTodoDateTime(
  value: string | Date | null,
  options?: {
    emptyText?: string
    invalidText?: string
  },
): string {
  if (!value) {
    return options?.emptyText ?? ''
  }

  const date = parseDateInput(value)
  if (!date) {
    return options?.invalidText ?? ''
  }

  return `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())} ${padNumber(date.getHours())}:${padNumber(date.getMinutes())}`
}

export function getTodoTrashExpireAt(deletedAt: string | Date | null): Date | null {
  const deletedDate = parseDateInput(deletedAt)
  if (!deletedDate) {
    return null
  }
  return new Date(deletedDate.getTime() + TODO_TRASH_RETENTION_DAYS * DAY_IN_MS)
}

export function getTodoTrashRemainingDeleteDays(deletedAt: string | Date | null): number | null {
  const expireAt = getTodoTrashExpireAt(deletedAt)
  if (!expireAt) {
    return null
  }

  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.max(0, Math.floor((expireAt.getTime() - todayStart.getTime()) / DAY_IN_MS))
}

export function getTodoTrashRemainingDeleteText(deletedAt: string | Date | null): string {
  const remainingDays = getTodoTrashRemainingDeleteDays(deletedAt)
  if (remainingDays === null) {
    return '等待自动删除'
  }
  return `还剩${remainingDays}天删除`
}

export function getTodoRecurrenceText(type: RecurrenceType | string, interval?: number): string {
  if (type === 'custom') {
    return `每${interval}天`
  }
  return todoRecurrenceOptions.find(option => option.value === type)?.label || type
}

export function shouldKeepTodoAccentColor(todo: Pick<Todo, 'status' | 'progress_reset_at' | 'end_date'>): boolean {
  if (todo.status !== 'done') {
    return false
  }

  const nextResetAt = parseDateInput(todo.progress_reset_at)
  if (!nextResetAt) {
    return false
  }

  const deadline = parseDateInput(todo.end_date)
  if (!deadline) {
    return true
  }

  return nextResetAt.getTime() <= deadline.getTime()
}

export function sortTodosByStatusAndPinCreated<T extends Pick<Todo, 'status' | 'is_pinned' | 'created_at'>>(todos: readonly T[]): T[] {
  return [...todos].sort((left, right) => {
    if (left.status !== right.status) {
      return left.status === 'todo' ? -1 : 1
    }
    if (left.is_pinned !== right.is_pinned) {
      return left.is_pinned ? -1 : 1
    }
    return new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
  })
}

