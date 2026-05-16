import type { TodoStatus } from '@personal-system/domain/todos'
import { ref } from 'vue'

export interface TodoListActionStore {
  completeTodo: (todoId: string) => Promise<unknown>
  fetchTodos: () => Promise<unknown>
  uncompleteTodo: (todoId: string) => Promise<unknown>
}

export interface TodoListActionMessages {
  loadFailed?: string
  toggleFailed?: string
}

export interface UseTodoListActionsOptions {
  messages?: TodoListActionMessages
}

const DEFAULT_MESSAGES: Required<TodoListActionMessages> = {
  loadFailed: '待办加载失败',
  toggleFailed: '待办状态更新失败',
}

export function useTodoListActions(store: TodoListActionStore, options?: UseTodoListActionsOptions) {
  const loading = ref(false)
  const errorMessage = ref('')
  const messages = {
    ...DEFAULT_MESSAGES,
    ...options?.messages,
  }

  function clearError() {
    errorMessage.value = ''
  }

  async function loadTodos() {
    loading.value = true
    clearError()

    try {
      await store.fetchTodos()
      return true
    } catch {
      errorMessage.value = messages.loadFailed
      return false
    } finally {
      loading.value = false
    }
  }

  async function toggleTodoStatus(todoId: string, status: TodoStatus) {
    clearError()

    try {
      if (status === 'done') {
        await store.uncompleteTodo(todoId)
      } else {
        await store.completeTodo(todoId)
      }
      return true
    } catch {
      errorMessage.value = messages.toggleFailed
      return false
    }
  }

  return {
    errorMessage,
    loading,
    clearError,
    loadTodos,
    toggleTodoStatus,
  }
}

