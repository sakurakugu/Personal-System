import { ElMessage, ElMessageBox } from 'element-plus'
import type { ComputedRef } from 'vue'
import { nextStatusLabel, statusOrder } from '../helpers/todo-item'
import type { Todo, TodoStatus, TodoUpdateParams } from '../store'
import { getApiErrorMessage } from '@personal-system/api'

export function useTodoPageBatchActions(options: {
  selectedTodos: ComputedRef<Todo[]>
  hasSelectedTodoNeedingDone: ComputedRef<boolean>
  hasSelectedTodoNeedingPin: ComputedRef<boolean>
  exitMultiSelect: () => void
  changeStatus: (todo: Todo, newStatus: TodoStatus) => Promise<void>
  updateTodo: (id: string, body: TodoUpdateParams) => Promise<unknown>
  deleteTodo: (id: string) => Promise<void>
  restoreTodo: (id: string) => Promise<unknown>
  permanentlyDeleteTodo: (id: string) => Promise<void>
  completeTodo: (id: string, occurredOn?: string) => Promise<unknown>
  uncompleteTodo: (id: string, occurredOn?: string) => Promise<unknown>
}) {
  async function batchChangeSelectedStatus() {
    const targetStatus: TodoStatus = options.hasSelectedTodoNeedingDone.value ? 'done' : 'todo'
    const targetTodos = options.selectedTodos.value.filter(todo => todo.status !== targetStatus)
    const count = targetTodos.length
    if (count === 0) {
      options.exitMultiSelect()
      return
    }

    try {
      await Promise.all(targetTodos.map(todo => options.changeStatus(todo, targetStatus)))
      ElMessage.success(`已批量${targetStatus === 'done' ? '完成' : '重置为待办'} ${count} 项`)
      options.exitMultiSelect()
    } catch {
      ElMessage.error('批量修改状态失败')
    }
  }

  async function batchTogglePinSelectedTodos() {
    const todos = [...options.selectedTodos.value]
    if (todos.length === 0) return

    const nextPinned = options.hasSelectedTodoNeedingPin.value
    const targetTodos = todos.filter(todo => todo.is_pinned !== nextPinned)
    if (targetTodos.length === 0) {
      options.exitMultiSelect()
      return
    }

    try {
      await Promise.all(targetTodos.map(todo => options.updateTodo(todo.id, { is_pinned: nextPinned })))
      ElMessage.success(`已批量${nextPinned ? '置顶' : '取消置顶'} ${targetTodos.length} 项`)
      options.exitMultiSelect()
    } catch {
      ElMessage.error('批量置顶失败')
    }
  }

  async function batchDeleteSelectedTodos() {
    const todos = [...options.selectedTodos.value]
    const count = todos.length
    if (count === 0) return

    try {
      await ElMessageBox.confirm(
        `确定将选中的 ${count} 项移至回收站吗？`,
        '批量删除',
        {
          type: 'warning',
          confirmButtonText: '确认删除',
          cancelButtonText: '取消',
        },
      )
    } catch {
      return
    }

    try {
      await Promise.all(todos.map(todo => options.deleteTodo(todo.id)))
      ElMessage.success(`已移至回收站 ${count} 项`)
      options.exitMultiSelect()
    } catch {
      ElMessage.error('批量删除失败')
    }
  }

  async function batchRestoreSelectedTodos() {
    const todos = [...options.selectedTodos.value]
    const count = todos.length
    if (count === 0) return

    try {
      await Promise.all(todos.map(todo => options.restoreTodo(todo.id)))
      ElMessage.success(`已恢复 ${count} 项`)
      options.exitMultiSelect()
    } catch {
      ElMessage.error('批量恢复失败')
    }
  }

  async function batchPermanentDeleteSelectedTodos() {
    const todos = [...options.selectedTodos.value]
    const count = todos.length
    if (count === 0) return

    try {
      await ElMessageBox.confirm(
        `确定永久删除选中的 ${count} 项吗？此操作不可恢复。`,
        '永久删除',
        {
          type: 'warning',
          confirmButtonText: '永久删除',
          cancelButtonText: '取消',
        },
      )
    } catch {
      return
    }

    try {
      await Promise.all(todos.map(todo => options.permanentlyDeleteTodo(todo.id)))
      ElMessage.success(`已永久删除 ${count} 项`)
      options.exitMultiSelect()
    } catch {
      ElMessage.error('批量永久删除失败')
    }
  }

  async function handleChangeStatusForComponent(todo: Todo) {
    const nextStatus = statusOrder[todo.status] as TodoStatus
    await options.changeStatus(todo, nextStatus)
    ElMessage.success(`${todo.title} 已${nextStatusLabel[todo.status]}`)
  }

  async function handleAdjustOccurrenceForComponent(
    todo: Todo,
    occurredOn: string,
    action: 'complete' | 'reset',
  ) {
    try {
      if (action === 'complete') {
        await options.completeTodo(todo.id, occurredOn)
        ElMessage.success(`已记录 ${todo.title} 在 ${occurredOn} 的完成`)
      } else {
        await options.uncompleteTodo(todo.id, occurredOn)
        ElMessage.success(`已重置 ${todo.title} 在 ${occurredOn} 的完成记录`)
      }
    } catch (error) {
      ElMessage.error(getApiErrorMessage(error, action === 'complete' ? '记录完成失败' : '重置完成记录失败'))
    }
  }

  return {
    batchChangeSelectedStatus,
    batchTogglePinSelectedTodos,
    batchDeleteSelectedTodos,
    batchRestoreSelectedTodos,
    batchPermanentDeleteSelectedTodos,
    handleChangeStatusForComponent,
    handleAdjustOccurrenceForComponent,
  }
}

