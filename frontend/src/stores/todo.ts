import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  completeTodo as requestCompleteTodo,
  createTodo,
  deleteTodo as requestDeleteTodo,
  fetchDeletedTodos as requestDeletedTodos,
  fetchTodos as requestTodos,
  restoreTodo as requestRestoreTodo,
  toggleTodoPin,
  uncompleteTodo as requestUncompleteTodo,
  updateTodo as requestUpdateTodo,
} from '../features/todos/api'
import type { TodoListQuery } from '../features/todos/types'
export type {
  CompletionHistoryDay,
  CompletionHistoryItem,
  CompletionHistoryResponse,
  RecurrenceType,
  Todo,
  TodoCreateParams,
  TodoStatus,
  TodoTransferItem,
  TodoTransferPayload,
  TodoUpdateParams,
} from '../features/todos/types'
import type {
  Todo,
  TodoCreateParams,
  TodoUpdateParams,
} from '../features/todos/types'

export const useTodoStore = defineStore('todo', () => {
  const todos = ref<Todo[]>([])
  const deletedTodos = ref<Todo[]>([])
  const loading = ref(false)
  const deletedLoaded = ref(false)

  // 获取待办列表（未删除的）
  async function fetchTodos(params?: TodoListQuery) {
    loading.value = true
    try {
      todos.value = await requestTodos(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchDeletedTodos() {
    loading.value = true
    try {
      deletedTodos.value = await requestDeletedTodos()
      deletedLoaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function addTodo(body: TodoCreateParams) {
    const data = await createTodo(body)
    todos.value.unshift(data)
    return data
  }

  async function updateTodo(id: string, body: TodoUpdateParams) {
    const data = await requestUpdateTodo(id, body)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) todos.value[idx] = data
    const deletedIdx = deletedTodos.value.findIndex(t => t.id === id)
    if (deletedIdx !== -1) deletedTodos.value[deletedIdx] = data
    return data
  }

  async function deleteTodo(id: string) {
    const target = todos.value.find(t => t.id === id) ?? null
    await requestDeleteTodo(id, false)
    todos.value = todos.value.filter(t => t.id !== id)
    if (target) {
      const deletedAt = new Date().toISOString()
      deletedTodos.value = [
        {
          ...target,
          is_deleted: true,
          deleted_at: deletedAt,
          updated_at: deletedAt,
        },
        ...deletedTodos.value.filter(t => t.id !== id),
      ]
      deletedLoaded.value = true
    }
  }

  async function permanentlyDeleteTodo(id: string) {
    await requestDeleteTodo(id, true)
    deletedTodos.value = deletedTodos.value.filter(t => t.id !== id)
  }

  async function restoreTodo(id: string) {
    const data = await requestRestoreTodo(id)
    deletedTodos.value = deletedTodos.value.filter(t => t.id !== id)
    todos.value.unshift(data)
    return data
  }

  async function togglePin(id: string) {
    const data = await toggleTodoPin(id)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) {
      todos.value[idx] = data
      todos.value.sort((a, b) => {
        if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
    }
    return data
  }

  async function toggleComplete(id: string) {
    const todo = todos.value.find(t => t.id === id)
    if (!todo) return
    if (todo.status === 'done') {
      return uncompleteTodo(id)
    } else {
      return completeTodo(id)
    }
  }

  async function completeTodo(id: string, occurredOn?: string) {
    const data = await requestCompleteTodo(id, occurredOn)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) todos.value[idx] = data
    return data
  }

  async function uncompleteTodo(id: string, occurredOn?: string) {
    const data = await requestUncompleteTodo(id, occurredOn)
    const idx = todos.value.findIndex(t => t.id === id)
    if (idx !== -1) todos.value[idx] = data
    return data
  }

  return {
    todos,
    deletedTodos,
    loading,
    deletedLoaded,
    fetchTodos,
    fetchDeletedTodos,
    addTodo,
    updateTodo,
    deleteTodo,
    permanentlyDeleteTodo,
    restoreTodo,
    togglePin,
    toggleComplete,
    completeTodo,
    uncompleteTodo,
  }
})
