import type {
  RecurrenceType,
  Todo,
  TodoStatus,
  TodoTransferItem,
  TodoTransferPayload,
} from '../types'

const VALID_RECURRENCE_TYPES = new Set<RecurrenceType>([
  'none',
  'daily',
  'weekly',
  'monthly',
  'yearly',
  'workday',
  'weekend',
  'holiday',
  'custom',
])

function normalizeTodoStatus(value: unknown): TodoStatus {
  return value === 'done' ? 'done' : 'todo'
}

function normalizeRecurrenceType(value: unknown): RecurrenceType {
  if (typeof value === 'string' && VALID_RECURRENCE_TYPES.has(value as RecurrenceType)) {
    return value as RecurrenceType
  }
  return 'none'
}

function normalizeNumber(value: unknown, fallback: number, options?: { min?: number; max?: number }): number {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return fallback
  }
  const min = options?.min ?? Number.NEGATIVE_INFINITY
  const max = options?.max ?? Number.POSITIVE_INFINITY
  return Math.min(max, Math.max(min, Math.round(value)))
}

function normalizeOptionalDate(value: unknown): string | undefined {
  if (typeof value !== 'string' || !value.trim()) {
    return undefined
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return undefined
  }
  return date.toISOString()
}

function normalizeTags(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .filter((tag): tag is string => typeof tag === 'string')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

export function normalizeTodoTransferItem(item: unknown): TodoTransferItem | null {
  if (!item || typeof item !== 'object') {
    return null
  }
  const record = item as Record<string, unknown>
  const title = typeof record.title === 'string' ? record.title.trim() : ''
  if (!title) {
    return null
  }

  const recurrenceType = normalizeRecurrenceType(record.recurrence_type)
  const timesPerInterval = normalizeNumber(record.times_per_interval, 1, { min: 1, max: 999 })

  return {
    title,
    description: typeof record.description === 'string' && record.description.trim() ? record.description.trim() : undefined,
    status: normalizeTodoStatus(record.status),
    importance: normalizeNumber(record.importance, 33, { min: 0, max: 100 }),
    urgency: normalizeNumber(record.urgency, 33, { min: 0, max: 100 }),
    start_date: normalizeOptionalDate(record.start_date),
    end_date: normalizeOptionalDate(record.end_date),
    is_pinned: Boolean(record.is_pinned),
    tags: normalizeTags(record.tags),
    recurrence_type: recurrenceType,
    recurrence_interval: normalizeNumber(record.recurrence_interval, 1, { min: 1, max: 365 }),
    recurrence_count: recurrenceType === 'none'
      ? 0
      : normalizeNumber(record.recurrence_count, 0, { min: -1, max: 999 }),
    times_per_interval: recurrenceType === 'none' ? 1 : timesPerInterval,
    interval_progress: recurrenceType === 'none'
      ? 0
      : normalizeNumber(record.interval_progress, 0, { min: 0, max: timesPerInterval }),
    is_deleted: Boolean(record.is_deleted),
  }
}

export function parseTodoTransferPayload(rawText: string): TodoTransferItem[] {
  const parsed = JSON.parse(rawText) as unknown
  const items = Array.isArray(parsed)
    ? parsed
    : parsed && typeof parsed === 'object' && Array.isArray((parsed as { todos?: unknown }).todos)
      ? (parsed as { todos: unknown[] }).todos
      : null

  if (!items) {
    throw new Error('导入文件格式不正确')
  }

  const normalized = items
    .map((item) => normalizeTodoTransferItem(item))
    .filter((item): item is TodoTransferItem => item !== null)

  if (normalized.length === 0) {
    throw new Error('导入文件中没有可用的待办事项')
  }

  return normalized
}

export function toTodoTransferItem(todo: Todo): TodoTransferItem {
  return {
    title: todo.title,
    description: todo.description ?? undefined,
    status: todo.status,
    importance: todo.importance,
    urgency: todo.urgency,
    start_date: todo.start_date ?? undefined,
    end_date: todo.end_date ?? undefined,
    is_pinned: todo.is_pinned,
    tags: todo.tags ?? [],
    recurrence_type: todo.recurrence_type,
    recurrence_interval: todo.recurrence_interval,
    recurrence_count: todo.recurrence_count,
    times_per_interval: todo.times_per_interval,
    interval_progress: todo.interval_progress,
    is_deleted: todo.is_deleted,
  }
}

function normalizeFingerprintDate(value: string | undefined): string {
  return normalizeOptionalDate(value) || ''
}

export function getTodoTransferFingerprint(todo: TodoTransferItem): string {
  return JSON.stringify({
    title: todo.title.trim(),
    description: todo.description?.trim() || '',
    status: todo.status,
    importance: todo.importance,
    urgency: todo.urgency,
    start_date: normalizeFingerprintDate(todo.start_date),
    end_date: normalizeFingerprintDate(todo.end_date),
    is_pinned: todo.is_pinned,
    tags: Array.from(new Set(todo.tags.map((tag) => tag.trim()).filter(Boolean))).sort(),
    recurrence_type: todo.recurrence_type,
    recurrence_interval: todo.recurrence_interval,
    recurrence_count: todo.recurrence_count,
    times_per_interval: todo.times_per_interval,
    interval_progress: todo.interval_progress,
    is_deleted: todo.is_deleted,
  })
}

export function getTodoFingerprint(todo: Todo): string {
  return getTodoTransferFingerprint(toTodoTransferItem(todo))
}

export function buildTodoTransferPayload(version: number, todos: Todo[]): TodoTransferPayload {
  return {
    version,
    exported_at: new Date().toISOString(),
    total: todos.length,
    todos: todos.map((todo) => toTodoTransferItem(todo)),
  }
}
