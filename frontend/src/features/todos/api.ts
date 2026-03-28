import api from '../../utils/api'
import type {
  CompletionHistoryResponse,
  Todo,
  TodoCreateParams,
  TodoListQuery,
  TodoUpdateParams,
} from './types'

function buildTodoQueryString(query: TodoListQuery & { is_deleted?: boolean }): string {
  const params = new URLSearchParams()
  params.append('is_deleted', String(query.is_deleted ?? false))
  if (query.status) params.append('status', query.status)
  if (query.is_pinned !== undefined) params.append('is_pinned', String(query.is_pinned))
  if (query.sort_by) params.append('sort_by', query.sort_by)
  if (query.sort_desc !== undefined) params.append('sort_desc', String(query.sort_desc))
  return params.toString()
}

export async function fetchTodos(query: TodoListQuery = {}): Promise<Todo[]> {
  const { data } = await api.get<Todo[]>(`/todos?${buildTodoQueryString(query)}`)
  return data
}

export async function fetchDeletedTodos(): Promise<Todo[]> {
  const { data } = await api.get<Todo[]>(`/todos?${buildTodoQueryString({ is_deleted: true })}`)
  return data
}

export async function createTodo(payload: TodoCreateParams): Promise<Todo> {
  const { data } = await api.post<Todo>('/todos', payload)
  return data
}

export async function updateTodo(id: string, payload: TodoUpdateParams): Promise<Todo> {
  const { data } = await api.patch<Todo>(`/todos/${id}`, payload)
  return data
}

export async function deleteTodo(id: string, permanent = false): Promise<void> {
  await api.delete(`/todos/${id}?permanent=${String(permanent)}`)
}

export async function restoreTodo(id: string): Promise<Todo> {
  const { data } = await api.post<Todo>(`/todos/${id}/restore`)
  return data
}

export async function toggleTodoPin(id: string): Promise<Todo> {
  const { data } = await api.post<Todo>(`/todos/${id}/toggle-pin`)
  return data
}

export async function completeTodo(id: string, occurredOn?: string): Promise<Todo> {
  const query = occurredOn ? `?occurred_on=${encodeURIComponent(occurredOn)}` : ''
  const { data } = await api.post<Todo>(`/todos/${id}/complete${query}`)
  return data
}

export async function uncompleteTodo(id: string, occurredOn?: string): Promise<Todo> {
  const query = occurredOn ? `?occurred_on=${encodeURIComponent(occurredOn)}` : ''
  const { data } = await api.post<Todo>(`/todos/${id}/uncomplete${query}`)
  return data
}

export async function fetchTodoCompletionHistory(startDate: string, endDate: string): Promise<CompletionHistoryResponse> {
  const { data } = await api.get<CompletionHistoryResponse>('/stats/todos/completion-history', {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  })
  return data
}
