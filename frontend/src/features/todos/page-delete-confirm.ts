/* global sessionStorage */
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

export type TodoDeleteMode = 'soft' | 'permanent'

const DELETE_CONFIRM_KEY = 'todo_delete_confirm_dont_ask'

function shouldSkipConfirm(): boolean {
  try {
    return sessionStorage.getItem(DELETE_CONFIRM_KEY) === 'true'
  } catch {
    return false
  }
}

function setDontAskAgain(value: boolean) {
  try {
    if (value) {
      sessionStorage.setItem(DELETE_CONFIRM_KEY, 'true')
    } else {
      sessionStorage.removeItem(DELETE_CONFIRM_KEY)
    }
  } catch {
    // ignore
  }
}

export function useTodoDeleteConfirm(options: {
  deleteTodo: (id: string) => Promise<void>
  permanentlyDeleteTodo: (id: string) => Promise<void>
}) {
  const showDeleteConfirm = ref(false)
  const todoToDelete = ref<string | null>(null)
  const deleteMode = ref<TodoDeleteMode>('soft')
  const dontAskAgain = ref(false)

  function handleDeleteRequest(id: string, mode: TodoDeleteMode = 'soft') {
    todoToDelete.value = id
    deleteMode.value = mode
    if (shouldSkipConfirm()) {
      void confirmDelete()
    } else {
      dontAskAgain.value = false
      showDeleteConfirm.value = true
    }
  }

  async function confirmDelete() {
    if (!todoToDelete.value) return

    setDontAskAgain(dontAskAgain.value)

    try {
      if (deleteMode.value === 'permanent') {
        await options.permanentlyDeleteTodo(todoToDelete.value)
        ElMessage.success('已永久删除')
      } else {
        await options.deleteTodo(todoToDelete.value)
        ElMessage.success('已移至回收站')
      }
    } catch {
      ElMessage.error('删除失败')
    }

    todoToDelete.value = null
    showDeleteConfirm.value = false
  }

  function cancelDelete() {
    todoToDelete.value = null
    showDeleteConfirm.value = false
  }

  return {
    showDeleteConfirm,
    deleteMode,
    dontAskAgain,
    handleDeleteRequest,
    confirmDelete,
    cancelDelete,
  }
}
