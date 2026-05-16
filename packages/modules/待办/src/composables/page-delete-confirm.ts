/* global sessionStorage */
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

export type TodoDeleteMode = 'soft' | 'permanent'

const DELETE_CONFIRM_KEY = 'todo_delete_confirm_dont_ask'

function 是否跳过确认(): boolean {
  try {
    return sessionStorage.getItem(DELETE_CONFIRM_KEY) === 'true'
  } catch {
    return false
  }
}

function 设置不再询问(value: boolean) {
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

export function 使用待办删除确认(options: {
  deleteTodo: (id: string) => Promise<void>
  permanentlyDeleteTodo: (id: string) => Promise<void>
}) {
  const showDeleteConfirm = ref(false)
  const todoToDelete = ref<string | null>(null)
  const deleteMode = ref<TodoDeleteMode>('soft')
  const dontAskAgain = ref(false)

  function 处理删除请求(id: string, mode: TodoDeleteMode = 'soft') {
    todoToDelete.value = id
    deleteMode.value = mode
    if (是否跳过确认()) {
      void 确认删除()
    } else {
      dontAskAgain.value = false
      showDeleteConfirm.value = true
    }
  }

  async function 确认删除() {
    if (!todoToDelete.value) return

    设置不再询问(dontAskAgain.value)

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

  function 取消删除() {
    todoToDelete.value = null
    showDeleteConfirm.value = false
  }

  return {
    showDeleteConfirm,
    deleteMode,
    dontAskAgain,
    handleDeleteRequest: 处理删除请求,
    confirmDelete: 确认删除,
    cancelDelete: 取消删除,
  }
}
