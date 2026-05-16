import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  完成待办 as 请求完成待办,
  创建待办,
  删除待办 as 请求删除待办,
  获取已删除待办 as 请求获取已删除待办,
  获取待办列表 as 请求获取待办列表,
  恢复待办 as 请求恢复待办,
  切换待办置顶,
  取消完成待办 as 请求取消完成待办,
  更新待办 as 请求更新待办,
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
      todos.value = await 请求获取待办列表(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchDeletedTodos() {
    loading.value = true
    try {
      deletedTodos.value = await 请求获取已删除待办()
      deletedLoaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function addTodo(body: TodoCreateParams) {
    const data = await 创建待办(body)
    todos.value.unshift(data)
    return data
  }

  async function updateTodo(id: string, body: TodoUpdateParams) {
    const data = await 请求更新待办(id, body)
    const idx = todos.value.findIndex((todo) => todo.id === id)
    if (idx !== -1) todos.value[idx] = data
    const deletedIdx = deletedTodos.value.findIndex((todo) => todo.id === id)
    if (deletedIdx !== -1) deletedTodos.value[deletedIdx] = data
    return data
  }

  async function deleteTodo(id: string) {
    const target = todos.value.find((todo) => todo.id === id) ?? null
    await 请求删除待办(id, false)
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
    await 请求删除待办(id, true)
    deletedTodos.value = deletedTodos.value.filter((todo) => todo.id !== id)
  }

  async function restoreTodo(id: string) {
    const data = await 请求恢复待办(id)
    deletedTodos.value = deletedTodos.value.filter((todo) => todo.id !== id)
    todos.value.unshift(data)
    return data
  }

  async function togglePin(id: string) {
    const data = await 切换待办置顶(id)
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
    const data = await 请求完成待办(id, occurredOn)
    const idx = todos.value.findIndex((todo) => todo.id === id)
    if (idx !== -1) todos.value[idx] = data
    return data
  }

  async function uncompleteTodo(id: string, occurredOn?: string) {
    const data = await 请求取消完成待办(id, occurredOn)
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
