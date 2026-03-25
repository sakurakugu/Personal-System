import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

// 循环类型
export type RecurrenceType = 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'workday' | 'weekend' | 'holiday' | 'custom'

// 待办事项状态
export type TodoStatus = 'todo' | 'in_progress' | 'done'

export interface Todo {
  id: string
  title: string
  description: string | null
  status: TodoStatus
  // 优先级双维度 (0-100)
  importance: number
  urgency: number
  // 时间范围
  start_date: string | null
  end_date: string | null
  // 标记
  is_pinned: boolean
  // 软删除
  is_deleted: boolean
  deleted_at: string | null
  // 标签（逗号分隔）
  tags: string | null
  // 循环设置
  recurrence_type: RecurrenceType
  recurrence_interval: number
  recurrence_count: number
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
  tags?: string
  recurrence_type?: RecurrenceType
  recurrence_interval?: number
  recurrence_count?: number
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
  tags?: string
  recurrence_type?: RecurrenceType
  recurrence_interval?: number
  recurrence_count?: number
}

export const useTodoStore = defineStore('todo', () => {
  const todos = ref<Todo[]>([])
  const deletedTodos = ref<Todo[]>([])
  const loading = ref(false)

  // 获取待办列表（未删除的）
  async function fetchTodos(params?: {
    status?: TodoStatus
    is_pinned?: boolean
    sort_by?: string
    sort_desc?: boolean
  }) {
    loading.value = true
    try {
      const query = new URLSearchParams()
      query.append('is_deleted', 'false')
      if (params?.status) query.append('status', params.status)
      if (params?.is_pinned !== undefined) query.append('is_pinned', String(params.is_pinned))
      if (params?.sort_by) query.append('sort_by', params.sort_by)
      if (params?.sort_desc !== undefined) query.append('sort_desc', String(params.sort_desc))
      
      const { data } = await api.get(`/todos?${query.toString()}`)
      todos.value = data
    } finally {
      loading.value = false
    }
  }

  // 获取已删除的待办（回收站）
  async function fetchDeletedTodos() {
    loading.value = true
    try {
      const { data } = await api.get('/todos?is_deleted=true')
      deletedTodos.value = data
    } finally {
      loading.value = false
    }
  }

  async function addTodo(body: TodoCreateParams) {
    const { data } = await api.post('/todos', body)
    todos.value.unshift(data)
    return data
  }

  async function updateTodo(id: string, body: TodoUpdateParams) {
    const { data } = await api.patch(`/todos/${id}`, body)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) todos.value[idx] = data
    return data
  }

  // 软删除
  async function deleteTodo(id: string) {
    await api.delete(`/todos/${id}?permanent=false`)
    todos.value = todos.value.filter(t => t.id !== id)
  }

  // 永久删除
  async function permanentlyDeleteTodo(id: string) {
    await api.delete(`/todos/${id}?permanent=true`)
    deletedTodos.value = deletedTodos.value.filter(t => t.id !== id)
  }

  // 从回收站恢复
  async function restoreTodo(id: string) {
    const { data } = await api.post(`/todos/${id}/restore`)
    deletedTodos.value = deletedTodos.value.filter(t => t.id !== id)
    todos.value.unshift(data)
    return data
  }

  // 切换置顶状态
  async function togglePin(id: string) {
    const { data } = await api.post(`/todos/${id}/toggle-pin`)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) {
      todos.value[idx] = data
      // 重新排序：置顶的在前面
      todos.value.sort((a, b) => {
        if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
    }
    return data
  }

  // 切换完成状态
  async function toggleComplete(id: string) {
    const todo = todos.value.find(t => t.id === id)
    if (!todo) return
    const newStatus: TodoStatus = todo.status === 'done' ? 'todo' : 'done'
    return updateTodo(id, { status: newStatus })
  }

  return {
    todos,
    deletedTodos,
    loading,
    fetchTodos,
    fetchDeletedTodos,
    addTodo,
    updateTodo,
    deleteTodo,
    permanentlyDeleteTodo,
    restoreTodo,
    togglePin,
    toggleComplete,
  }
})
