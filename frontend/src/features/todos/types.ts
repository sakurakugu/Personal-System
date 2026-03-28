export type RecurrenceType =
  | 'none'
  | 'daily'
  | 'weekly'
  | 'monthly'
  | 'yearly'
  | 'workday'
  | 'weekend'
  | 'holiday'
  | 'custom'

export type TodoStatus = 'todo' | 'done'

export interface Todo {
  id: string
  title: string
  description: string | null
  status: TodoStatus
  importance: number
  urgency: number
  start_date: string | null
  end_date: string | null
  is_pinned: boolean
  is_deleted: boolean
  deleted_at: string | null
  tags: string[] | null
  recurrence_type: RecurrenceType
  recurrence_interval: number
  recurrence_count: number
  times_per_interval: number
  interval_progress: number
  progress_reset_at: string | null
  created_at: string
  updated_at: string
}

export interface TodoCreateParams {
  title: string
  description?: string
  importance?: number
  urgency?: number
  start_date?: string
  end_date?: string
  is_pinned?: boolean
  tags?: string[]
  recurrence_type?: RecurrenceType
  recurrence_interval?: number
  recurrence_count?: number
  times_per_interval?: number
}

export interface TodoUpdateParams {
  title?: string
  description?: string
  status?: TodoStatus
  importance?: number
  urgency?: number
  start_date?: string
  end_date?: string
  is_pinned?: boolean
  is_deleted?: boolean
  tags?: string[]
  recurrence_type?: RecurrenceType
  recurrence_interval?: number
  recurrence_count?: number
  times_per_interval?: number
  interval_progress?: number
}

export interface TodoListQuery {
  status?: TodoStatus
  is_pinned?: boolean
  sort_by?: string
  sort_desc?: boolean
}

export interface CompletionHistoryItem {
  todo_id: string
  title: string
  completed_count: number
}

export interface CompletionHistoryDay {
  date: string
  completed_count: number
  items: CompletionHistoryItem[]
}

export interface CompletionHistoryResponse {
  start_date: string
  end_date: string
  max_completed_count: number
  total_completed_count: number
  days: CompletionHistoryDay[]
}

export interface TodoTransferItem {
  title: string
  description?: string
  status: TodoStatus
  importance: number
  urgency: number
  start_date?: string
  end_date?: string
  is_pinned: boolean
  tags: string[]
  recurrence_type: RecurrenceType
  recurrence_interval: number
  recurrence_count: number
  times_per_interval: number
  interval_progress: number
  is_deleted: boolean
}

export interface TodoTransferPayload {
  version: number
  exported_at: string
  total: number
  todos: TodoTransferItem[]
}
