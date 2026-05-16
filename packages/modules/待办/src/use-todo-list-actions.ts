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

export function 使用待办列表操作(store: TodoListActionStore, options?: UseTodoListActionsOptions) {
  const loading = ref(false)
  const errorMessage = ref('')
  const messages = {
    ...DEFAULT_MESSAGES,
    ...options?.messages,
  }

  function 清除错误() {
    errorMessage.value = ''
  }

  async function 加载待办() {
    loading.value = true
    清除错误()

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

  async function 切换待办状态(todoId: string, status: TodoStatus) {
    清除错误()

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
    clearError: 清除错误,
    loadTodos: 加载待办,
    toggleTodoStatus: 切换待办状态,
  }
}

