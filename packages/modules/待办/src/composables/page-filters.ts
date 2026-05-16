import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { recurrenceOptions, 按状态和置顶创建排序待办, statusLabel } from '../helpers/todo-item'
import type { Todo, TodoStatus, RecurrenceType } from '../store'

export type TodoViewMode = 'list' | 'cards' | 'quadrants' | 'heatmap' | 'gantt' | 'important'
export type TodoPinFilter = 'all' | 'pinned' | 'unpinned'
export type TodoRecurrenceFilter = 'all' | 'recurring' | RecurrenceType

export const todoStatusFilterKeys: TodoStatus[] = ['todo', 'done']

export const todoPinFilterLabel: Record<TodoPinFilter, string> = {
  all: '全部',
  pinned: '仅置顶',
  unpinned: '未置顶',
}

function 标准化搜索文本(value: string | null | undefined): string {
  return value?.trim().toLowerCase() ?? ''
}

export function 是否为重要日待办(todo: Todo): boolean {
  if (!todo.tags) return false
  return todo.tags.includes('重要日')
}

export function 使用待办页面过滤器(options: {
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

  function 切换状态(status: TodoStatus) {
    const index = selectedStatuses.value.indexOf(status)
    if (index > -1) {
      if (selectedStatuses.value.length > 1) {
        selectedStatuses.value.splice(index, 1)
      }
    } else {
      selectedStatuses.value.push(status)
    }
  }

  function 选择所有状态() {
    selectedStatuses.value = [...todoStatusFilterKeys]
  }

  function 是否状态已选择(status: TodoStatus): boolean {
    return selectedStatuses.value.includes(status)
  }

  function 匹配搜索(todo: Todo): boolean {
    const keyword = 标准化搜索文本(searchKeyword.value)
    if (!keyword) {
      return true
    }
    const searchFields = [
      todo.title,
      todo.description ?? '',
      ...(todo.tags ?? []),
    ]
    return 标准化搜索文本(searchFields.join(' ')).includes(keyword)
  }

  function 匹配置顶(todo: Todo): boolean {
    if (pinFilter.value === 'pinned') {
      return todo.is_pinned
    }
    if (pinFilter.value === 'unpinned') {
      return !todo.is_pinned
    }
    return true
  }

  function 匹配循环(todo: Todo): boolean {
    if (recurrenceFilter.value === 'all') {
      return true
    }
    if (recurrenceFilter.value === 'recurring') {
      return todo.recurrence_type !== 'none'
    }
    return todo.recurrence_type === recurrenceFilter.value
  }

  function 匹配标签(todo: Todo): boolean {
    if (selectedTags.value.length === 0) {
      return true
    }
    const todoTags = todo.tags ?? []
    return selectedTags.value.some(tag => todoTags.includes(tag))
  }

  function 匹配高级筛选(todo: Todo): boolean {
    return 匹配搜索(todo) && 匹配置顶(todo) && 匹配循环(todo) && 匹配标签(todo)
  }

  function 匹配状态(todo: Todo): boolean {
    if (options.viewMode.value === 'important') {
      return true
    }
    return selectedStatuses.value.includes(todo.status)
  }

  function 移除选中标签(tag: string) {
    selectedTags.value = selectedTags.value.filter(item => item !== tag)
  }

  function 重置高级筛选() {
    searchKeyword.value = ''
    pinFilter.value = 'all'
    recurrenceFilter.value = 'all'
    selectedTags.value = []
  }

  function 重置所有筛选() {
    重置高级筛选()
    选择所有状态()
  }

  const importantTodos = computed(() => options.todos.value.filter(是否为重要日待办))
  const normalTodos = computed(() => options.todos.value.filter(todo => !是否为重要日待办(todo)))
  const deletedNormalSourceTodos = computed(() => (
    options.deletedTodos.value.filter(todo => !是否为重要日待办(todo))
  ))
  const deletedImportantSourceTodos = computed(() => (
    options.deletedTodos.value.filter(是否为重要日待办)
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
    filterSourceTodos.value.filter(todo => 匹配高级筛选(todo))
  ))

  const statusGroups = computed(() => ({
    todo: filteredSourceTodosBeforeStatus.value.filter(todo => todo.status === 'todo'),
    done: filteredSourceTodosBeforeStatus.value.filter(todo => todo.status === 'done'),
  }))

  const filteredNormalTodos = computed(() => (
    按状态和置顶创建排序待办(normalTodos.value.filter(todo => 匹配高级筛选(todo) && 匹配状态(todo)))
  ))
  const filteredImportantTodos = computed(() => (
    按状态和置顶创建排序待办(importantTodos.value.filter(todo => 匹配高级筛选(todo) && 匹配状态(todo)))
  ))
  const filteredDeletedNormalTodos = computed(() => (
    按状态和置顶创建排序待办(deletedNormalSourceTodos.value.filter(todo => 匹配高级筛选(todo) && 匹配状态(todo)))
  ))
  const filteredDeletedImportantTodos = computed(() => (
    按状态和置顶创建排序待办(deletedImportantSourceTodos.value.filter(todo => 匹配高级筛选(todo) && 匹配状态(todo)))
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
    toggleStatus: 切换状态,
    selectAllStatuses: 选择所有状态,
    isStatusSelected: 是否状态已选择,
    removeSelectedTag: 移除选中标签,
    resetAdvancedFilters: 重置高级筛选,
    resetAllFilters: 重置所有筛选,
  }
}
