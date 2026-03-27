import type { Todo, TodoCreateParams, TodoStatus, TodoUpdateParams, RecurrenceType } from '../stores/todo'

export interface TodoFormState {
  title: string
  description: string
  importance: number
  urgency: number
  start_date: Date | null
  start_time: Date | null
  end_date: Date | null
  end_time: Date | null
  is_pinned: boolean
  tags: string
  recurrence_type: RecurrenceType
  recurrence_interval: number
  recurrence_count: number
  times_per_interval: number
}

export interface TodoEditFormState extends TodoFormState {
  status: TodoStatus
}

export const importanceMarks = { 0: '不重要', 33: '一般', 66: '重要', 100: '非常重要' }
export const urgencyMarks = { 0: '不紧急', 33: '一般', 66: '紧急', 100: '非常紧急' }

export function createEmptyTodoForm(): TodoFormState {
  return {
    title: '',
    description: '',
    importance: 33,
    urgency: 33,
    start_date: null,
    start_time: null,
    end_date: null,
    end_time: null,
    is_pinned: false,
    tags: '',
    recurrence_type: 'none',
    recurrence_interval: 1,
    recurrence_count: 0,
    times_per_interval: 1,
  }
}

export function createEmptyTodoEditForm(): TodoEditFormState {
  return {
    ...createEmptyTodoForm(),
    status: 'todo',
  }
}

export function combineDateTime(date: Date | null, time: Date | null): string | undefined {
  if (!date) return undefined
  const combinedDate = new Date(date)
  if (time) {
    const timeValue = new Date(time)
    combinedDate.setHours(timeValue.getHours(), timeValue.getMinutes(), 0, 0)
  }
  return combinedDate.toISOString()
}

export function splitDateTime(isoString: string | null): { date: Date | null, time: Date | null } {
  if (!isoString) return { date: null, time: null }
  const value = new Date(isoString)
  return {
    date: new Date(value.getFullYear(), value.getMonth(), value.getDate()),
    time: new Date(2000, 0, 1, value.getHours(), value.getMinutes()),
  }
}

export function parseTagsInput(tagsText: string): string[] {
  return tagsText.split(/[,，]/).map(tag => tag.trim()).filter(Boolean)
}

export function formatTagsInput(tags: string[] | null): string {
  if (!tags) return ''
  return tags.join(',')
}

export function buildTodoCreatePayload(form: TodoFormState): TodoCreateParams {
  return {
    title: form.title,
    description: form.description || undefined,
    importance: form.importance,
    urgency: form.urgency,
    start_date: combineDateTime(form.start_date, form.start_time),
    end_date: combineDateTime(form.end_date, form.end_time),
    is_pinned: form.is_pinned,
    tags: parseTagsInput(form.tags),
    recurrence_type: form.recurrence_type,
    recurrence_interval: form.recurrence_interval,
    recurrence_count: form.recurrence_count,
    times_per_interval: form.times_per_interval,
  }
}

export function buildTodoUpdatePayload(form: TodoEditFormState): TodoUpdateParams {
  return {
    ...buildTodoCreatePayload(form),
    status: form.status,
  }
}

export function createTodoEditFormFromTodo(todo: Todo): TodoEditFormState {
  const start = splitDateTime(todo.start_date)
  const end = splitDateTime(todo.end_date)

  return {
    title: todo.title,
    description: todo.description || '',
    status: todo.status,
    importance: todo.importance,
    urgency: todo.urgency,
    start_date: start.date,
    start_time: start.time,
    end_date: end.date,
    end_time: end.time,
    is_pinned: todo.is_pinned,
    tags: formatTagsInput(todo.tags),
    recurrence_type: todo.recurrence_type,
    recurrence_interval: todo.recurrence_interval,
    recurrence_count: todo.recurrence_count,
    times_per_interval: todo.times_per_interval,
  }
}
