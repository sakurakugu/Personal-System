import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { recurrenceOptions, sortTodosByStatusAndPinCreated, statusLabel } from '../../helpers/todo-item'
import type { Todo, TodoStatus, RecurrenceType } from '../../store'

export type TodoViewMode = 'list' | 'cards' | 'quadrants' | 'heatmap' | 'gantt' | 'important'
export type TodoPinFilter = 'all' | 'pinned' | 'unpinned'
export type TodoRecurrenceFilter = 'all' | 'recurring' | RecurrenceType

export const todoStatusFilterKeys: TodoStatus[] = ['todo', 'done']

export const todoPinFilterLabel: Record<TodoPinFilter, string> = {
  all: '全部',
  pinned: '仅置顶',
  unpinned: '未置顶',
}

function normalizeSearchText(value: string | null | undefined): string {
  return value?.trim().toLowerCase() ?? ''
}

export function isImportantDayTodo(todo: Todo): boolean {
  if (!todo.tags) return false
  return todo.tags.includes('重要日')
}

export function useTodoPageFilters(options: {
  todos: Ref<Todo[]> | ComputedRef<Todo[]>
  deletedTodos: Ref<Todo[]> | ComputedRef<Todo[]>
  viewMode: Ref<TodoViewMode>
  showRecycleBin: Ref<boolean>
}) {
  const selectedStatuses = ref<TodoStatus[]>(['todo', 'done'])
  const searchKeyword = ref('')
  const pinFilter = ref<TodoPinFilter>('all')
  const recurrenceFilter = ref<TodoRecurrenceFilter>('all')
  const selectedTags = ref<string[]>([])

  function toggleStatus(status: TodoStatus) {
    const index = selectedStatuses.value.indexOf(status)
    if (index > -1) {
      if (selectedStatuses.value.length > 1) {
        selectedStatuses.value.splice(index, 1)
      }
    } else {
      selectedStatuses.value.push(status)
    }
  }

  function selectAllStatuses() {
    selectedStatuses.value = [...todoStatusFilterKeys]
  }

  function isStatusSelected(status: TodoStatus): boolean {
    return selectedStatuses.value.includes(status)
  }

  function matchesSearch(todo: Todo): boolean {
    const keyword = normalizeSearchText(searchKeyword.value)
    if (!keyword) {
      return true
    }
    const searchFields = [
      todo.title,
      todo.description ?? '',
      ...(todo.tags ?? []),
    ]
    return normalizeSearchText(searchFields.join(' ')).includes(keyword)
  }

  function matchesPin(todo: Todo): boolean {
    if (pinFilter.value === 'pinned') {
      return todo.is_pinned
    }
    if (pinFilter.value === 'unpinned') {
      return !todo.is_pinned
    }
    return true
  }

  function matchesRecurrence(todo: Todo): boolean {
    if (recurrenceFilter.value === 'all') {
      return true
    }
    if (recurrenceFilter.value === 'recurring') {
      return todo.recurrence_type !== 'none'
    }
    return todo.recurrence_type === recurrenceFilter.value
  }

  function matchesTags(todo: Todo): boolean {
    if (selectedTags.value.length === 0) {
      return true
    }
    const todoTags = todo.tags ?? []
    return selectedTags.value.some(tag => todoTags.includes(tag))
  }

  function matchesAdvancedFilters(todo: Todo): boolean {
    return matchesSearch(todo) && matchesPin(todo) && matchesRecurrence(todo) && matchesTags(todo)
  }

  function matchesStatus(todo: Todo): boolean {
    if (options.viewMode.value === 'important') {
      return true
    }
    return selectedStatuses.value.includes(todo.status)
  }

  function removeSelectedTag(tag: string) {
    selectedTags.value = selectedTags.value.filter(item => item !== tag)
  }

  function resetAdvancedFilters() {
    searchKeyword.value = ''
    pinFilter.value = 'all'
    recurrenceFilter.value = 'all'
    selectedTags.value = []
  }

  function resetAllFilters() {
    resetAdvancedFilters()
    selectAllStatuses()
  }

  const importantTodos = computed(() => options.todos.value.filter(isImportantDayTodo))
  const normalTodos = computed(() => options.todos.value.filter(todo => !isImportantDayTodo(todo)))
  const deletedNormalSourceTodos = computed(() => (
    options.deletedTodos.value.filter(todo => !isImportantDayTodo(todo))
  ))
  const deletedImportantSourceTodos = computed(() => (
    options.deletedTodos.value.filter(isImportantDayTodo)
  ))

  const filterSourceTodos = computed(() => {
    if (options.showRecycleBin.value) {
      return options.viewMode.value === 'important'
        ? deletedImportantSourceTodos.value
        : deletedNormalSourceTodos.value
    }
    return options.viewMode.value === 'important' ? importantTodos.value : normalTodos.value
  })

  const filteredSourceTodosBeforeStatus = computed(() => (
    filterSourceTodos.value.filter(todo => matchesAdvancedFilters(todo))
  ))

  const statusGroups = computed(() => ({
    todo: filteredSourceTodosBeforeStatus.value.filter(todo => todo.status === 'todo'),
    done: filteredSourceTodosBeforeStatus.value.filter(todo => todo.status === 'done'),
  }))

  const filteredNormalTodos = computed(() => (
    sortTodosByStatusAndPinCreated(normalTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
  ))
  const filteredImportantTodos = computed(() => (
    sortTodosByStatusAndPinCreated(importantTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
  ))
  const filteredDeletedNormalTodos = computed(() => (
    sortTodosByStatusAndPinCreated(deletedNormalSourceTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
  ))
  const filteredDeletedImportantTodos = computed(() => (
    sortTodosByStatusAndPinCreated(deletedImportantSourceTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
  ))

  const isImportantRecycleBinView = computed(() => (
    options.showRecycleBin.value && options.viewMode.value === 'important'
  ))

  const currentTodos = computed(() => {
    if (options.showRecycleBin.value) {
      return options.viewMode.value === 'important'
        ? filteredDeletedImportantTodos.value
        : filteredDeletedNormalTodos.value
    }
    return filteredNormalTodos.value
  })

  const visibleTodoCount = computed(() => {
    if (options.showRecycleBin.value) {
      return currentTodos.value.length
    }
    return options.viewMode.value === 'important'
      ? filteredImportantTodos.value.length
      : filteredNormalTodos.value.length
  })

  const hasSearchKeyword = computed(() => Boolean(searchKeyword.value.trim()))
  const extraFilterCount = computed(() => {
    return Number(pinFilter.value !== 'all')
      + Number(recurrenceFilter.value !== 'all')
      + Number(selectedTags.value.length > 0)
  })
  const hasAnyFilters = computed(() => {
    return hasSearchKeyword.value
      || extraFilterCount.value > 0
      || (options.viewMode.value !== 'important' && selectedStatuses.value.length !== 2)
  })

  const filterButtonText = computed(() => {
    if (options.viewMode.value === 'important') {
      return '全部'
    }
    if (selectedStatuses.value.length === 2) {
      return '全部'
    }
    const order: TodoStatus[] = ['todo', 'done']
    const selected = order.filter(status => selectedStatuses.value.includes(status))
    return selected.map(status => statusLabel[status]).join('/') || '请选择'
  })

  const recurrenceFilterLabel = computed(() => {
    if (recurrenceFilter.value === 'all') {
      return '全部'
    }
    if (recurrenceFilter.value === 'recurring') {
      return '仅循环'
    }
    return recurrenceOptions.find(item => item.value === recurrenceFilter.value)?.label ?? '未知'
  })

  return {
    selectedStatuses,
    searchKeyword,
    pinFilter,
    recurrenceFilter,
    selectedTags,
    importantTodos,
    filteredNormalTodos,
    filteredImportantTodos,
    filteredDeletedNormalTodos,
    filteredDeletedImportantTodos,
    isImportantRecycleBinView,
    currentTodos,
    statusGroups,
    visibleTodoCount,
    hasSearchKeyword,
    extraFilterCount,
    hasAnyFilters,
    filterButtonText,
    recurrenceFilterLabel,
    toggleStatus,
    selectAllStatuses,
    isStatusSelected,
    removeSelectedTag,
    resetAdvancedFilters,
    resetAllFilters,
  }
}
