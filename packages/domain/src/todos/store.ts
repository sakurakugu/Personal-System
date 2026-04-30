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
} from './api'
import type { TodoListQuery } from './types'

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
} from './types'
import type {
  Todo,
  TodoCreateParams,
  TodoUpdateParams,
} from './types'

export const useTodoStore = defineStore('todo', () => {
  const todos = ref<Todo[]>([])
  const deletedTodos = ref<Todo[]>([])
  const loading = ref(false)
  const deletedLoaded = ref(false)

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
    const idx = todos.value.findIndex((todo) => todo.id === id)
    if (idx !== -1) todos.value[idx] = data
    const deletedIdx = deletedTodos.value.findIndex((todo) => todo.id === id)
    if (deletedIdx !== -1) deletedTodos.value[deletedIdx] = data
    return data
  }

  async function deleteTodo(id: string) {
    const target = todos.value.find((todo) => todo.id === id) ?? null
    await requestDeleteTodo(id, false)
    todos.value = todos.value.filter((todo) => todo.id !== id)
    if (target) {
      const deletedAt = new Date().toISOString()
      deletedTodos.value = [
        {
          ...target,
          is_deleted: true,
          deleted_at: deletedAt,
          updated_at: deletedAt,
        },
        ...deletedTodos.value.filter((todo) => todo.id !== id),
      ]
      deletedLoaded.value = true
    }
  }

  async function permanentlyDeleteTodo(id: string) {
    await requestDeleteTodo(id, true)
    deletedTodos.value = deletedTodos.value.filter((todo) => todo.id !== id)
  }

  async function restoreTodo(id: string) {
    const data = await requestRestoreTodo(id)
    deletedTodos.value = deletedTodos.value.filter((todo) => todo.id !== id)
    todos.value.unshift(data)
    return data
  }

  async function togglePin(id: string) {
    const data = await toggleTodoPin(id)
    const idx = todos.value.findIndex((todo) => todo.id === id)
    if (idx !== -1) {
      todos.value[idx] = data
      todos.value.sort((left, right) => {
        if (left.is_pinned !== right.is_pinned) return left.is_pinned ? -1 : 1
        return new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
      })
    }
    return data
  }

  async function toggleComplete(id: string) {
    const todo = todos.value.find((item) => item.id === id)
    if (!todo) return
    if (todo.status === 'done') {
      return uncompleteTodo(id)
    }
    return completeTodo(id)
  }

  async function completeTodo(id: string, occurredOn?: string) {
    const data = await requestCompleteTodo(id, occurredOn)
    const idx = todos.value.findIndex((todo) => todo.id === id)
    if (idx !== -1) todos.value[idx] = data
    return data
  }

  async function uncompleteTodo(id: string, occurredOn?: string) {
    const data = await requestUncompleteTodo(id, occurredOn)
    const idx = todos.value.findIndex((todo) => todo.id === id)
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
