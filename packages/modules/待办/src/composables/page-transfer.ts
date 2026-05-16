/* global Blob, URL, HTMLInputElement */
import { ElMessage } from 'element-plus'
import { computed, ref, type Ref } from 'vue'
import {
  buildTodoTransferPayload,
  getTodoFingerprint,
  getTodoTransferFingerprint,
  parseTodoTransferPayload,
} from '../helpers/transfer'
import type { Todo, TodoCreateParams, TodoUpdateParams } from '../store'
import { getApiErrorMessage } from '@personal-system/api'

export function useTodoPageTransfer(options: {
  todos: Ref<Todo[]>
  deletedTodos: Ref<Todo[]>
  deletedLoaded: Ref<boolean>
  todoImportInput: Ref<HTMLInputElement | null>
  closeTransferDialog: () => void
  fetchDeletedTodos: () => Promise<void>
  addTodo: (body: TodoCreateParams) => Promise<Todo>
  updateTodo: (id: string, body: TodoUpdateParams) => Promise<unknown>
  deleteTodo: (id: string) => Promise<void>
}) {
  const includeDeletedTodosInExport = ref(false)
  const isImportingTodos = ref(false)
  const exportTodoTotal = computed(() => (
    options.todos.value.length + (includeDeletedTodosInExport.value ? options.deletedTodos.value.length : 0)
  ))

  async function exportTodos() {
    if (includeDeletedTodosInExport.value && !options.deletedLoaded.value) {
      await options.fetchDeletedTodos()
    }

    const todosToExport = includeDeletedTodosInExport.value
      ? [...options.todos.value, ...options.deletedTodos.value]
      : options.todos.value

    const payload = buildTodoTransferPayload(1, todosToExport)
    const content = JSON.stringify(payload, null, 2)
    const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const today = new Date().toISOString().slice(0, 10)

    link.href = url
    link.download = includeDeletedTodosInExport.value ? `todos-${today}-with-trash.json` : `todos-${today}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success(includeDeletedTodosInExport.value ? `已导出 ${payload.total} 条待办（含回收站）` : `已导出 ${payload.total} 条待办`)
  }

  function triggerTodoImport() {
    options.todoImportInput.value?.click()
  }

  async function handleTodoImport(event: Event) {
    const input = event.target as HTMLInputElement | null
    if (!input) {
      return
    }

    const file = input.files?.[0]
    if (!file) {
      return
    }

    let importedCount = 0
    let mergedCount = 0
    isImportingTodos.value = true

    try {
      const text = await file.text()
      const todosToImport = parseTodoTransferPayload(text)
      const hasDeletedItems = todosToImport.some(item => item.is_deleted)
      if (hasDeletedItems && !options.deletedLoaded.value) {
        await options.fetchDeletedTodos()
      }
      const existingFingerprints = new Set([
        ...options.todos.value.map(todo => getTodoFingerprint(todo)),
        ...options.deletedTodos.value.map(todo => getTodoFingerprint(todo)),
      ])

      for (const [index, item] of todosToImport.entries()) {
        const fingerprint = getTodoTransferFingerprint(item)
        if (existingFingerprints.has(fingerprint)) {
          mergedCount += 1
          continue
        }

        try {
          const created = await options.addTodo({
            title: item.title,
            description: item.description,
            importance: item.importance,
            urgency: item.urgency,
            start_date: item.start_date,
            end_date: item.end_date,
            is_pinned: item.is_pinned,
            tags: item.tags,
            recurrence_type: item.recurrence_type,
            recurrence_interval: item.recurrence_interval,
            recurrence_count: item.recurrence_count,
            times_per_interval: item.times_per_interval,
          })

          if (item.status !== 'todo' || item.interval_progress > 0) {
            await options.updateTodo(created.id, {
              status: item.status,
              interval_progress: item.interval_progress,
            })
          }
          if (item.is_deleted) {
            await options.deleteTodo(created.id)
          }

          existingFingerprints.add(fingerprint)
          importedCount += 1
        } catch (error) {
          throw new Error(`第 ${index + 1} 条导入失败：${getApiErrorMessage(error, '请检查待办字段')}`, { cause: error })
        }
      }

      options.closeTransferDialog()
      ElMessage.success(
        mergedCount > 0
          ? `已导入 ${importedCount} 条，合并 ${mergedCount} 条重复待办`
          : `已导入 ${importedCount} 条待办`,
      )
    } catch (error) {
      ElMessage.error(
        error instanceof Error
          ? `${importedCount > 0 ? `已导入 ${importedCount} 条，` : ''}${mergedCount > 0 ? `已合并 ${mergedCount} 条重复待办，` : ''}${error.message}`
          : '导入失败',
      )
    } finally {
      isImportingTodos.value = false
      input.value = ''
    }
  }

  return {
    includeDeletedTodosInExport,
    isImportingTodos,
    exportTodoTotal,
    exportTodos,
    triggerTodoImport,
    handleTodoImport,
  }
}

