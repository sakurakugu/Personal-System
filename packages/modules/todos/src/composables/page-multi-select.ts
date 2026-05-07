import { computed, ref, watch, type ComputedRef } from 'vue'
import type { Todo } from '../store'

export function useTodoPageMultiSelect(options: {
  visibleTodosForMultiSelect: ComputedRef<Todo[]>
  allTodos: ComputedRef<Todo[]>
}) {
  const multiSelectedIds = ref<string[]>([])
  const visibleTodoIdSet = computed(() => new Set(options.visibleTodosForMultiSelect.value.map(todo => todo.id)))
  const selectedTodoIdSet = computed(() => new Set(multiSelectedIds.value))
  const isMultiSelectMode = ref(false)

  const selectedTodos = computed(() => {
    const todoMap = new Map(options.allTodos.value.map(todo => [todo.id, todo]))
    return multiSelectedIds.value
      .map(id => todoMap.get(id))
      .filter((todo): todo is Todo => Boolean(todo))
  })

  const selectedVisibleTodos = computed(() => (
    options.visibleTodosForMultiSelect.value.filter(todo => selectedTodoIdSet.value.has(todo.id))
  ))

  const allVisibleSelected = computed(() => (
    options.visibleTodosForMultiSelect.value.length > 0
    && selectedVisibleTodos.value.length === options.visibleTodosForMultiSelect.value.length
  ))

  const hasSelectedTodoNeedingPin = computed(() => selectedTodos.value.some(todo => !todo.is_pinned))
  const hasSelectedTodoNeedingDone = computed(() => selectedTodos.value.some(todo => todo.status !== 'done'))
  const multiSelectPinLabel = computed(() => (
    hasSelectedTodoNeedingPin.value ? '置顶' : '取消置顶'
  ))
  const multiSelectActionLabel = computed(() => (
    hasSelectedTodoNeedingDone.value ? '设为完成' : '设为待办'
  ))

  watch(visibleTodoIdSet, (idSet) => {
    multiSelectedIds.value = multiSelectedIds.value.filter(id => idSet.has(id))
  })

  function enterMultiSelect(todo: Todo) {
    isMultiSelectMode.value = true
    if (!selectedTodoIdSet.value.has(todo.id)) {
      multiSelectedIds.value = [...multiSelectedIds.value, todo.id]
    }
  }

  function toggleMultiSelect(todo: Todo) {
    isMultiSelectMode.value = true
    if (selectedTodoIdSet.value.has(todo.id)) {
      multiSelectedIds.value = multiSelectedIds.value.filter(id => id !== todo.id)
      return
    }
    multiSelectedIds.value = [...multiSelectedIds.value, todo.id]
  }

  function exitMultiSelect() {
    isMultiSelectMode.value = false
    multiSelectedIds.value = []
  }

  function toggleSelectAllVisibleTodos() {
    if (allVisibleSelected.value) {
      multiSelectedIds.value = multiSelectedIds.value.filter(id => !visibleTodoIdSet.value.has(id))
      return
    }
    multiSelectedIds.value = options.visibleTodosForMultiSelect.value.map(todo => todo.id)
  }

  return {
    multiSelectedIds,
    selectedTodoIdSet,
    isMultiSelectMode,
    selectedTodos,
    allVisibleSelected,
    hasSelectedTodoNeedingPin,
    hasSelectedTodoNeedingDone,
    multiSelectPinLabel,
    multiSelectActionLabel,
    enterMultiSelect,
    toggleMultiSelect,
    exitMultiSelect,
    toggleSelectAllVisibleTodos,
  }
}
