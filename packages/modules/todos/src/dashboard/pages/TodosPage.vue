<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, clearTimeout, HTMLInputElement */
import { onBeforeUnmount, onMounted, ref, computed, nextTick, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  ElButton,
  ElCheckbox,
  ElDatePicker,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElPopover,
  ElSelect,
  ElSlider,
  ElSwitch,
  ElTag,
  ElTimePicker,
} from 'element-plus'
import { List, CircleCheckFilled, WarningFilled, Grid, Menu, Delete, Calendar, Timer, Filter, Star, Download, Upload, Search, ArrowLeft, Select, CloseBold, RefreshRight } from '@element-plus/icons-vue'
import {
  todoPinFilterLabel,
  todoStatusFilterKeys,
  useTodoPageFilters,
  type TodoViewMode,
} from '../composables/page-filters'
import { useTodoDeleteConfirm } from '../composables/page-delete-confirm'
import { useTodoPageMultiSelect } from '../composables/page-multi-select'
import { useTodoPageBatchActions } from '../composables/page-batch-actions'
import { useTodoPageTransfer } from '../composables/page-transfer'
import { useTodoStore, type Todo, type TodoStatus, type TodoCreateParams, type TodoUpdateParams } from '../../store'
import { BaseDialog, SegmentedSwitch, TagInlineInput } from '@personal-system/ui'
import TodoCards from '../components/TodoCards.vue'
import TodoQuadrants from '../components/TodoQuadrants.vue'
import TodoList from '../components/TodoList.vue'
import TodoHeatmap from '../components/TodoHeatmap.vue'
import TodoGantt from '../components/TodoGantt.vue'
import ImportantDays from '../components/ImportantDays.vue'
import ImportantDayForm from '../components/ImportantDayForm.vue'
import { recurrenceOptions, statusLabel } from '../../helpers/todo-item'
import {
  buildTodoCreatePayload,
  buildTodoUpdatePayload,
  createEmptyTodoEditForm,
  createEmptyTodoForm,
  createTodoEditFormFromTodo,
  importanceMarks,
  parseTagsInput,
  urgencyMarks,
} from '../../helpers/todo-form'

const todoStore = useTodoStore()
const { todos, deletedTodos, deletedLoaded } = storeToRefs(todoStore)

const showAdd = ref(false)
const showEdit = ref(false)
const editingTodo = ref<Todo | null>(null)
const showRecycleBin = ref(false)
const showImportantDayForm = ref(false)
const editingImportantDay = ref<Todo | null>(null)
const showTransferDialog = ref(false)
const todoImportInput = ref<HTMLInputElement | null>(null)
type InputInstance = InstanceType<typeof ElInput>
const newTodoTitleInputRef = ref<InputInstance | null>(null)

let createButtonLongPressTimer: ReturnType<typeof setTimeout> | null = null
let ignoreNextCreateClick = false

const CREATE_BUTTON_LONG_PRESS_MS = 600

// 视图模式：list-列表, cards-卡片瀑布流, quadrants-四象限, heatmap-热力图, gantt-甘特图, important-重要日
const viewMode = ref<TodoViewMode>('list')

const 视图切换选项 = [
  { value: 'list', label: '', title: '列表视图', icon: List },
  { value: 'cards', label: '', title: '卡片视图', icon: Grid },
  { value: 'quadrants', label: '', title: '四象限视图', icon: Menu },
  { value: 'heatmap', label: '', title: '热力图视图', icon: Calendar },
  { value: 'gantt', label: '', title: '时间条视图', icon: Timer },
  { value: 'important', label: '', title: '重要日', icon: Star },
] as const satisfies readonly { value: TodoViewMode, label: string, title: string, icon: typeof List }[]

const 回收站视图切换选项 = [
  { value: 'list', label: '待办列表', title: '待办列表', icon: List },
  { value: 'important', label: '重要日', title: '重要日', icon: Star },
] as const satisfies readonly { value: Extract<TodoViewMode, 'list' | 'important'>, label: string, title: string, icon: typeof List }[]


// 新建表单
const newTodo = ref(createEmptyTodoForm())

// 编辑表单
const editForm = ref(createEmptyTodoEditForm())

const {
  selectedStatuses,
  searchKeyword,
  pinFilter,
  recurrenceFilter,
  selectedTags,
  filteredNormalTodos,
  filteredImportantTodos,
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
} = useTodoPageFilters({
  todos,
  deletedTodos,
  viewMode,
  showRecycleBin,
})

const {
  showDeleteConfirm,
  deleteMode,
  dontAskAgain,
  handleDeleteRequest,
  confirmDelete,
  cancelDelete,
} = useTodoDeleteConfirm({
  deleteTodo: (id) => todoStore.deleteTodo(id),
  permanentlyDeleteTodo: (id) => todoStore.permanentlyDeleteTodo(id),
})

const {
  includeDeletedTodosInExport,
  isImportingTodos,
  exportTodoTotal,
  exportTodos,
  triggerTodoImport,
  handleTodoImport,
} = useTodoPageTransfer({
  todos,
  deletedTodos,
  deletedLoaded,
  todoImportInput,
  closeTransferDialog: () => {
    showTransferDialog.value = false
  },
  fetchDeletedTodos: () => todoStore.fetchDeletedTodos(),
  addTodo: (body) => todoStore.addTodo(body),
  updateTodo: (id, body) => todoStore.updateTodo(id, body),
  deleteTodo: (id) => todoStore.deleteTodo(id),
})

onMounted(() => {
  todoStore.fetchTodos()
})

onBeforeUnmount(() => {
  clearCreateButtonLongPress()
})

watch(includeDeletedTodosInExport, async (value) => {
  if (!value) {
    return
  }
  if (!deletedLoaded.value) {
    await todoStore.fetchDeletedTodos()
  }
})

watch([viewMode, showRecycleBin], () => {
  exitMultiSelect()
})

const visibleTodosForMultiSelect = computed(() => {
  if (viewMode.value === 'important') {
    return showRecycleBin.value ? filteredDeletedImportantTodos.value : filteredImportantTodos.value
  }
  if (viewMode.value === 'heatmap') {
    return filteredNormalTodos.value
  }
  return currentTodos.value
})
const allTodosForMultiSelect = computed(() => [...todos.value, ...deletedTodos.value])
const {
  multiSelectedIds,
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
} = useTodoPageMultiSelect({
  visibleTodosForMultiSelect,
  allTodos: allTodosForMultiSelect,
})

const statusFilterKeys = todoStatusFilterKeys
const pinFilterLabel = todoPinFilterLabel

const statusIcon: Record<TodoStatus, typeof List> = {
  todo: List,
  done: CircleCheckFilled,
}

async function addTodo(keepDialogOpen = false) {
  if (!newTodo.value.title.trim()) return
  try {
    await todoStore.addTodo(buildTodoCreatePayload(newTodo.value))
    if (keepDialogOpen) {
      resetNewTodo()
      focusNewTodoTitleInput()
    } else {
      showAdd.value = false
      resetNewTodo()
    }
    ElMessage.success('创建成功')
  } catch {
    ElMessage.error('创建失败')
  }
}

function clearCreateButtonLongPress() {
  if (createButtonLongPressTimer !== null) {
    clearTimeout(createButtonLongPressTimer)
    createButtonLongPressTimer = null
  }
}

function openTransferDialog() {
  showTransferDialog.value = true
}

function startCreateButtonLongPress(event: Event) {
  if (event instanceof MouseEvent && event.button !== 0) {
    return
  }
  clearCreateButtonLongPress()
  createButtonLongPressTimer = setTimeout(() => {
    ignoreNextCreateClick = true
    openTransferDialog()
  }, CREATE_BUTTON_LONG_PRESS_MS)
}

function cancelCreateButtonLongPress() {
  clearCreateButtonLongPress()
}

function handleCreateButtonClick() {
  clearCreateButtonLongPress()
  if (ignoreNextCreateClick) {
    ignoreNextCreateClick = false
    return
  }
  if (viewMode.value === 'important') {
    openImportantDayForm()
    return
  }
  showAdd.value = true
}

function resetNewTodo() {
  newTodo.value = createEmptyTodoForm()
}

function focusNewTodoTitleInput() {
  void nextTick(() => {
    newTodoTitleInputRef.value?.focus()
    newTodoTitleInputRef.value?.input?.focus()
  })
}

// 打开重要日专用表单
function openImportantDayForm(todo?: Todo) {
  editingImportantDay.value = todo || null
  showImportantDayForm.value = true
}

// 处理重要日表单提交
async function handleImportantDaySubmit(data: {
  title: string
  description?: string
  dateType: 'start' | 'end'
  date: Date | null
  recurrenceType: string
  recurrenceInterval: number
}) {
  const basePayload = {
    title: data.title,
    tags: ['重要日'],
    recurrence_type: data.recurrenceType as any,
    recurrence_interval: data.recurrenceInterval,
    recurrence_count: -1,
    times_per_interval: 1,
    importance: 50,
    urgency: 50,
  }

  let payload: TodoCreateParams | TodoUpdateParams
  
  if (data.dateType === 'start') {
    // 正计时：设置开始日期，清除截止日期
    payload = {
      ...basePayload,
      description: data.description,
      start_date: data.date?.toISOString(),
      end_date: undefined,
    }
  } else {
    // 倒计时：设置截止日期，清除开始日期
    payload = {
      ...basePayload,
      description: data.description,
      start_date: undefined,
      end_date: data.date?.toISOString(),
    }
  }

  try {
    if (editingImportantDay.value) {
      // 编辑模式
      await todoStore.updateTodo(editingImportantDay.value.id, payload)
      ElMessage.success('保存成功')
    } else {
      // 新建模式
      await todoStore.addTodo(payload as TodoCreateParams)
      ElMessage.success('创建成功')
    }
    showImportantDayForm.value = false
    editingImportantDay.value = null
  } catch {
    ElMessage.error(editingImportantDay.value ? '保存失败' : '创建失败')
  }
}

function openEdit(todo: Todo) {
  editingTodo.value = todo
  editForm.value = createTodoEditFormFromTodo(todo)
  showEdit.value = true
}

async function saveEdit() {
  if (!editingTodo.value || !editForm.value.title.trim()) return
  try {
    await todoStore.updateTodo(editingTodo.value.id, buildTodoUpdatePayload(editForm.value))
    showEdit.value = false
    editingTodo.value = null
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  }
}

async function changeStatus(todo: Todo, newStatus: TodoStatus) {
  if (newStatus === 'done') {
    await todoStore.completeTodo(todo.id)
  } else {
    await todoStore.uncompleteTodo(todo.id)
  }
}

async function handleTogglePin(todo: Todo) {
  await todoStore.togglePin(todo.id)
}

async function handleRestore(id: string) {
  try {
    await todoStore.restoreTodo(id)
    ElMessage.success('已恢复')
  } catch {
    ElMessage.error('恢复失败')
  }
}

const {
  batchChangeSelectedStatus,
  batchTogglePinSelectedTodos,
  batchDeleteSelectedTodos,
  batchRestoreSelectedTodos,
  batchPermanentDeleteSelectedTodos,
  handleChangeStatusForComponent,
  handleAdjustOccurrenceForComponent,
} = useTodoPageBatchActions({
  selectedTodos,
  hasSelectedTodoNeedingDone,
  hasSelectedTodoNeedingPin,
  exitMultiSelect,
  changeStatus,
  updateTodo: (id, body) => todoStore.updateTodo(id, body),
  deleteTodo: (id) => todoStore.deleteTodo(id),
  restoreTodo: (id) => todoStore.restoreTodo(id),
  permanentlyDeleteTodo: (id) => todoStore.permanentlyDeleteTodo(id),
  completeTodo: (id, occurredOn) => todoStore.completeTodo(id, occurredOn),
  uncompleteTodo: (id, occurredOn) => todoStore.uncompleteTodo(id, occurredOn),
})

// 打开回收站
async function openRecycleBin() {
  showRecycleBin.value = true
  if (!deletedLoaded.value) {
    await todoStore.fetchDeletedTodos()
  }
}

// 关闭回收站
function closeRecycleBin() {
  showRecycleBin.value = false
}

// 禁用开始日期之后的日期（用于截止日期选择）
function disabledEndDate(endDate: Date, startDate: Date | null): boolean {
  if (!startDate) return false
  // 将日期转换为当天0点进行比较
  const start = new Date(startDate)
  start.setHours(0, 0, 0, 0)
  const end = new Date(endDate)
  end.setHours(0, 0, 0, 0)
  return end.getTime() < start.getTime()
}

// 禁用截止日期之前的日期（用于开始日期选择）
function disabledStartDate(startDate: Date, endDate: Date | null): boolean {
  if (!endDate) return false
  const start = new Date(startDate)
  start.setHours(0, 0, 0, 0)
  const end = new Date(endDate)
  end.setHours(0, 0, 0, 0)
  return start.getTime() > end.getTime()
}

// 获取所有已存在的标签（去重）
const allExistingTags = computed(() => {
  const allTags = new Set<string>()
  todos.value.forEach(todo => {
    if (todo.tags) {
      todo.tags.forEach(tag => {
        allTags.add(tag)
      })
    }
  })
  return Array.from(allTags).sort()
})

const suggestableTags = computed(() => allExistingTags.value.filter(tag => tag !== '重要日'))

// 获取当前表单中未使用的已存在标签
function getAvailableTags(currentTagsStr: string): string[] {
  const currentTags = new Set(parseTagsInput(currentTagsStr))
  return suggestableTags.value.filter(tag => !currentTags.has(tag))
}

// 添加标签到当前表单
function addTagToForm(formTags: string, tag: string): string {
  const tags = parseTagsInput(formTags)
  if (!tags.includes(tag)) {
    tags.push(tag)
  }
  return tags.join(',')
}

const newTodoAvailableTags = computed(() => getAvailableTags(newTodo.value.tags))
const editTodoAvailableTags = computed(() => getAvailableTags(editForm.value.tags))

</script>

<template>
  <div class="todos-page">
    <div class="todos-header">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><List /></ElIcon>
        <span>{{ showRecycleBin ? (viewMode === 'important' ? '重要日回收站' : '待办回收站') : (viewMode === 'important' ? '重要日' : '待办事项') }}</span>
      </h2>
      <div style="display: flex; gap: 8px">
        <ElButton v-if="showRecycleBin" @click="closeRecycleBin">
          <ElIcon><ArrowLeft /></ElIcon>返回列表
        </ElButton>
        <div
          v-if="!showRecycleBin"
          class="create-button-wrapper"
          @touchstart.passive="startCreateButtonLongPress"
          @touchmove="cancelCreateButtonLongPress"
          @touchend="cancelCreateButtonLongPress"
          @touchcancel="cancelCreateButtonLongPress"
          @mousedown="startCreateButtonLongPress"
          @mouseup="cancelCreateButtonLongPress"
          @mouseleave="cancelCreateButtonLongPress"
          @contextmenu.prevent
        >
          <ElButton type="primary" title="长按可导入或导出待办" @click="handleCreateButtonClick">+ 新建</ElButton>
        </div>
      </div>
    </div>

    <!-- 状态筛选、视图切换和回收站入口 -->
    <div class="status-bar">
      <div class="status-bar-left">
        <div class="filter-tools">
          <ElInput
            v-model="searchKeyword"
            class="todo-search-input"
            clearable
            placeholder="搜索标题、描述、标签"
          >
            <template #prefix>
              <ElIcon><Search /></ElIcon>
            </template>
          </ElInput>

          <div class="filter-button-group">
            <ElPopover trigger="click" :width="180" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
              <template #reference>
                <ElButton>
                  <span style="display: flex; align-items: center; gap: 6px">
                    <ElIcon><List /></ElIcon>
                    <span>
                      {{ filterButtonText }}
                      ({{ visibleTodoCount }})
                    </span>
                    <span style="margin-left: 4px">▼</span>
                  </span>
                </ElButton>
              </template>
              <div class="status-filter-list">
                <div
                  v-if="viewMode === 'important'"
                  class="status-filter-item is-selected"
                  @click="selectAllStatuses"
                >
                  <span
                    class="status-filter-text"
                  >
                    <ElIcon><List /></ElIcon>
                    <span>全部</span>
                    <span class="status-count">({{ visibleTodoCount }})</span>
                  </span>
                </div>
                <div v-else class="status-filter-options">
                  <div
                    v-for="key in statusFilterKeys"
                    :key="key"
                    class="status-filter-item"
                    :class="{ 'is-selected': isStatusSelected(key) }"
                    @click="toggleStatus(key)"
                  >
                    <span class="status-filter-text">
                      <ElIcon><component :is="statusIcon[key]" /></ElIcon>
                      <span>{{ statusLabel[key] }}</span>
                      <span class="status-count">({{ statusGroups[key].length }})</span>
                    </span>
                  </div>
                </div>
                <template v-if="!showRecycleBin">
                  <div class="status-filter-divider" />
                  <div class="status-filter-item" @click="openRecycleBin">
                    <span class="status-filter-text">
                      <ElIcon><Delete /></ElIcon>
                      <span>回收站</span>
                    </span>
                  </div>
                </template>
                <template v-else>
                  <div class="status-filter-divider" />
                  <div class="status-filter-item" @click="closeRecycleBin">
                    <span class="status-filter-text">
                      <ElIcon><ArrowLeft /></ElIcon>
                      <span>返回列表</span>
                    </span>
                  </div>
                </template>
              </div>
            </ElPopover>

            <ElPopover trigger="click" :width="280" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
              <template #reference>
                <ElButton>
                  <span style="display: flex; align-items: center; gap: 6px">
                    <ElIcon><Filter /></ElIcon>
                    <span>{{ extraFilterCount > 0 ? `更多筛选(${extraFilterCount})` : '更多筛选' }}</span>
                    <span style="margin-left: 4px">▼</span>
                  </span>
                </ElButton>
              </template>
              <div class="advanced-filter-panel">
                <div class="advanced-filter-field">
                  <span class="advanced-filter-label">置顶</span>
                  <ElSelect v-model="pinFilter" size="small">
                    <ElOption
                      v-for="(label, value) in pinFilterLabel"
                      :key="value"
                      :label="label"
                      :value="value"
                    />
                  </ElSelect>
                </div>

                <div class="advanced-filter-field">
                  <span class="advanced-filter-label">循环</span>
                  <ElSelect v-model="recurrenceFilter" size="small">
                    <ElOption label="全部" value="all" />
                    <ElOption label="仅循环" value="recurring" />
                    <ElOption label="不循环" value="none" />
                    <ElOption
                      v-for="item in recurrenceOptions.filter(option => option.value !== 'none')"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </ElSelect>
                </div>

                <div class="advanced-filter-field">
                  <span class="advanced-filter-label">标签</span>
                  <ElSelect
                    v-model="selectedTags"
                    multiple
                    collapse-tags
                    collapse-tags-tooltip
                    clearable
                    filterable
                    size="small"
                    placeholder="命中任一标签"
                  >
                    <ElOption
                      v-for="tag in suggestableTags"
                      :key="tag"
                      :label="tag"
                      :value="tag"
                    />
                  </ElSelect>
                  <span class="advanced-filter-hint">选中多个标签时，命中任一标签即保留。</span>
                </div>

                <div class="advanced-filter-actions">
                  <ElButton link @click="resetAdvancedFilters">重置筛选</ElButton>
                </div>
              </div>
            </ElPopover>
          </div>
        </div>

        <div v-if="hasAnyFilters" class="active-filters">
          <ElTag v-if="hasSearchKeyword" closable @close="searchKeyword = ''">
            搜索：{{ searchKeyword.trim() }}
          </ElTag>
          <ElTag v-if="viewMode !== 'important' && selectedStatuses.length !== 2" closable @close="selectAllStatuses()">
            状态：{{ filterButtonText }}
          </ElTag>
          <ElTag v-if="pinFilter !== 'all'" closable @close="pinFilter = 'all'">
            置顶：{{ pinFilterLabel[pinFilter] }}
          </ElTag>
          <ElTag v-if="recurrenceFilter !== 'all'" closable @close="recurrenceFilter = 'all'">
            循环：{{ recurrenceFilterLabel }}
          </ElTag>
          <ElTag
            v-for="tag in selectedTags"
            :key="`active-filter-${tag}`"
            closable
            @close="removeSelectedTag(tag)"
          >
            标签：{{ tag }}
          </ElTag>
          <ElButton link class="filter-reset-button" @click="resetAllFilters">清空全部</ElButton>
        </div>
      </div>
      
      <!-- 视图切换按钮 -->
      <SegmentedSwitch
        v-model="viewMode"
        class="view-toggle"
        aria-label="待办视图切换"
        :options="showRecycleBin ? 回收站视图切换选项 : 视图切换选项"
        active-color="var(--el-color-primary)"
      />
    </div>

    <!-- 待办回收站或列表视图 -->
    <div v-if="viewMode === 'list' || (showRecycleBin && viewMode !== 'important')" class="todo-view-container">
      <TodoList
        :todos="currentTodos"
        :show-recycle-bin="showRecycleBin"
        :multi-select-mode="isMultiSelectMode"
        :selected-ids="multiSelectedIds"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id, mode) => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
        @long-press="enterMultiSelect"
        @toggle-select="toggleMultiSelect"
      />
    </div>

    <!-- 卡片瀑布流视图 -->
    <div v-else-if="viewMode === 'cards' && !showRecycleBin" class="todo-view-container">
      <TodoCards
        :todos="currentTodos"
        :show-recycle-bin="showRecycleBin"
        :multi-select-mode="isMultiSelectMode"
        :selected-ids="multiSelectedIds"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id, mode) => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
        @long-press="enterMultiSelect"
        @toggle-select="toggleMultiSelect"
      />
      <div v-if="currentTodos.length === 0" class="todo-empty">
        <ElEmpty description="暂无数据" />
      </div>
    </div>

    <!-- 四象限视图 -->
    <div
      v-else-if="viewMode === 'quadrants' && !showRecycleBin"
      class="todo-view-container todo-view-container--quadrants"
    >
      <TodoQuadrants
        :todos="currentTodos"
        :show-recycle-bin="showRecycleBin"
        :multi-select-mode="isMultiSelectMode"
        :selected-ids="multiSelectedIds"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id, mode) => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
        @long-press="enterMultiSelect"
        @toggle-select="toggleMultiSelect"
      />
    </div>

    <!-- 热力图视图 -->
    <div v-else-if="viewMode === 'heatmap' && !showRecycleBin" class="todo-view-container">
      <TodoHeatmap
        :todos="filteredNormalTodos"
        :multi-select-mode="isMultiSelectMode"
        :selected-ids="multiSelectedIds"
        @toggle-complete="handleChangeStatusForComponent"
        @edit="openEdit"
        @long-press="enterMultiSelect"
        @toggle-select="toggleMultiSelect"
      />
    </div>

    <!-- 甘特图视图 -->
    <div v-else-if="viewMode === 'gantt' && !showRecycleBin" class="todo-view-container">
      <TodoGantt
        :todos="currentTodos"
        :multi-select-mode="isMultiSelectMode"
        :selected-ids="multiSelectedIds"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id: string, mode: 'soft' | 'permanent') => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
        @adjust-occurrence="handleAdjustOccurrenceForComponent"
        @long-press="enterMultiSelect"
        @toggle-select="toggleMultiSelect"
      />
    </div>

    <!-- 重要日视图 -->
    <div v-else-if="viewMode === 'important'" class="todo-view-container">
      <ImportantDays
        :todos="isImportantRecycleBinView ? filteredDeletedImportantTodos : filteredImportantTodos"
        :show-recycle-bin="showRecycleBin"
        :multi-select-mode="isMultiSelectMode"
        :selected-ids="multiSelectedIds"
        @edit="(todo: Todo) => openImportantDayForm(todo)"
        @toggle-pin="handleTogglePin"
        @delete="(id: string, mode: 'soft' | 'permanent') => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
        @long-press="enterMultiSelect"
        @toggle-select="toggleMultiSelect"
      />
    </div>

    <div v-if="isMultiSelectMode" class="multi-select-toolbar">
      <div class="multi-select-toolbar__summary">
        <ElIcon><Select /></ElIcon>
        <span>已选择 {{ multiSelectedIds.length }} 项</span>
      </div>
      <div class="multi-select-toolbar__actions">
        <ElButton @click="toggleSelectAllVisibleTodos">
          {{ allVisibleSelected ? '取消全选' : '全选当前视图' }}
        </ElButton>
        <ElButton @click="exitMultiSelect">
          <ElIcon><CloseBold /></ElIcon>
          退出多选
        </ElButton>
        <template v-if="showRecycleBin">
          <ElButton type="success" @click="batchRestoreSelectedTodos">
            <ElIcon><RefreshRight /></ElIcon>
            恢复
          </ElButton>
          <ElButton type="danger" class="multi-select-danger-button" @click="batchPermanentDeleteSelectedTodos">
            <ElIcon><Delete /></ElIcon>
            永久删除
          </ElButton>
        </template>
        <template v-else>
          <ElButton @click="batchTogglePinSelectedTodos">
            <ElIcon><Star /></ElIcon>
            {{ multiSelectPinLabel }}
          </ElButton>
          <ElButton type="primary" @click="batchChangeSelectedStatus">
            <ElIcon><CircleCheckFilled /></ElIcon>
            {{ multiSelectActionLabel }}
          </ElButton>
          <ElButton type="danger" class="multi-select-danger-button" @click="batchDeleteSelectedTodos">
            <ElIcon><Delete /></ElIcon>
            删除
          </ElButton>
        </template>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <BaseDialog
      v-model="showDeleteConfirm"
      title="确认删除"
      width="360px"
      style="max-width: 90vw"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0">
        <ElIcon :size="40" color="#f56c6c"><WarningFilled /></ElIcon>
        <span>
          {{ deleteMode === 'permanent' ? '确定要永久删除吗？此操作不可恢复！' : '确定要删除这个待办事项吗？' }}
        </span>
      </div>
      <div style="margin-top: 16px; padding-left: 52px">
        <ElCheckbox v-model="dontAskAgain">本次都不再询问（刷新后恢复）</ElCheckbox>
      </div>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <ElButton @click="cancelDelete">取消</ElButton>
          <ElButton :type="deleteMode === 'permanent' ? 'danger' : 'primary'" @click="confirmDelete">
            {{ deleteMode === 'permanent' ? '永久删除' : '删除' }}
          </ElButton>
        </div>
      </template>
    </BaseDialog>

    <!-- 导入导出对话框 -->
    <BaseDialog
      v-model="showTransferDialog"
      title="待办导入 / 导出"
      width="460px"
      style="max-width: 90vw"
    >
      <div class="todo-transfer-dialog">
        <div class="todo-transfer-tip">
          长按“新建”可打开此弹窗。导入会追加到当前用户的待办列表，不会清空现有数据；若业务内容完全一致，会自动合并去重。导出默认不包含回收站，开启开关后才会一并导出已删除待办。
        </div>
        <div class="todo-transfer-count">
          当前可导出 {{ exportTodoTotal }} 条待办{{ includeDeletedTodosInExport ? '（含回收站）' : '' }}
        </div>
        <div class="todo-transfer-actions">
          <ElButton class="todo-transfer-action" type="primary" plain @click="exportTodos">
            <span class="todo-transfer-action-content">
              <span class="todo-transfer-action-head">
                <ElIcon><Download /></ElIcon>
                <span class="todo-transfer-action-label">一键导出</span>
              </span>
              <span class="todo-transfer-action-desc">{{ includeDeletedTodosInExport ? '导出当前用户的待办和回收站为 JSON 文件' : '导出当前用户的正常待办为 JSON 文件' }}</span>
            </span>
          </ElButton>
          <ElButton class="todo-transfer-action" type="success" plain :loading="isImportingTodos" @click="triggerTodoImport">
            <span class="todo-transfer-action-content">
              <span class="todo-transfer-action-head">
                <ElIcon><Upload /></ElIcon>
                <span class="todo-transfer-action-label">一键导入</span>
              </span>
              <span class="todo-transfer-action-desc">选择导出的 JSON 文件并追加导入到当前账号</span>
            </span>
          </ElButton>
        </div>
        <div class="todo-transfer-options">
          <span class="todo-transfer-options-label">包含回收站</span>
          <ElSwitch v-model="includeDeletedTodosInExport" />
        </div>
      </div>
      <input
        ref="todoImportInput"
        class="todo-import-input"
        type="file"
        accept=".json,application/json"
        @change="handleTodoImport"
      >
    </BaseDialog>

    <!-- 新建对话框 -->
    <BaseDialog
      v-model="showAdd"
      :title="newTodo.tags.includes('重要日') ? '新建重要日' : '新建待办'"
      width="600px"
      style="max-width: 90vw"
      @opened="focusNewTodoTitleInput"
      @closed="resetNewTodo"
    >
      <ElForm label-position="left" label-width="80px" @submit.prevent="() => addTodo()">
        <ElFormItem>
          <template #label>
            <span>标题<span style="color: var(--el-color-danger); margin-left: 2px">*</span></span>
          </template>
          <ElInput
            ref="newTodoTitleInputRef"
            v-model="newTodo.title"
            placeholder="待办标题"
          />
        </ElFormItem>
        
        <ElFormItem label="描述">
          <ElInput v-model="newTodo.description" type="textarea" :rows="2" placeholder="可选描述" />
        </ElFormItem>

        <ElFormItem label="重要性">
          <ElSlider v-model="newTodo.importance" :min="0" :max="100" :marks="importanceMarks" show-stops />
        </ElFormItem>

        <ElFormItem label="紧急性">
          <ElSlider v-model="newTodo.urgency" :min="0" :max="100" :marks="urgencyMarks" show-stops />
        </ElFormItem>
        
        <ElFormItem label="时间">
          <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
            <div style="display: flex; gap: 4px; flex: 1; min-width: 200px">
              <ElDatePicker 
                v-model="newTodo.start_date" 
                type="date" 
                placeholder="开始日期" 
                clearable 
                style="width: 53%"
                :disabled-date="(date: Date) => disabledStartDate(date, newTodo.end_date)"
              />
              <ElTimePicker v-model="newTodo.start_time" placeholder="时间" clearable style="width: 47%" />
            </div>
            <span style="font-size: 14px; padding: 0 4px; opacity: 0.7">至</span>
            <div style="display: flex; gap: 4px; flex: 1; min-width: 200px">
              <ElDatePicker 
                v-model="newTodo.end_date" 
                type="date" 
                placeholder="截止日期" 
                clearable 
                style="width: 53%"
                :disabled-date="(date: Date) => disabledEndDate(date, newTodo.start_date)"
              />
              <ElTimePicker v-model="newTodo.end_time" placeholder="时间" clearable style="width: 47%" />
            </div>
          </div>
        </ElFormItem>

        <ElFormItem label="标签">
          <TagInlineInput v-model="newTodo.tags" :existing-tags="allExistingTags" placeholder="标签，用逗号分隔" />
          <div v-if="newTodoAvailableTags.length > 0" class="existing-tags">
            <ElTag
              v-for="tag in newTodoAvailableTags"
              :key="tag"
              size="small"
              effect="plain"
              class="existing-tag"
              @click="newTodo.tags = addTagToForm(newTodo.tags, tag)"
            >
              {{ tag }}
            </ElTag>
          </div>
        </ElFormItem>

        <ElFormItem label="循环">
          <div style="display: flex; gap: 12px; align-items: center; width: 100%">
            <ElSelect v-model="newTodo.recurrence_type" :style="{ flex: newTodo.recurrence_type === 'custom' ? '0 0 140px' : '1' }">
              <ElOption v-for="item in recurrenceOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
            <div v-if="newTodo.recurrence_type === 'custom'" style="display: flex; align-items: center; gap: 8px; flex-shrink: 0">
              <span class="recurrence-text">每</span>
              <ElInputNumber v-model="newTodo.recurrence_interval" :min="1" :max="365" style="width: 130px" />
              <span class="recurrence-text">天</span>
            </div>
          </div>
        </ElFormItem>

        <template v-if="newTodo.recurrence_type !== 'none'">
          <ElFormItem label="循环次数">
            <div style="display: flex; align-items: center; gap: 12px">
              <ElInputNumber v-model="newTodo.recurrence_count" :min="-1" :max="999" />
              <span style="font-size: 12px; opacity: 0.7">-1=无限，0=不循环</span>
            </div>
          </ElFormItem>
          <ElFormItem label="每天完成">
            <div style="display: flex; align-items: center; gap: 12px">
              <ElInputNumber v-model="newTodo.times_per_interval" :min="1" :max="999" />
              <span style="font-size: 12px; opacity: 0.7">次</span>
            </div>
          </ElFormItem>
        </template>

        <div style="display: flex; gap: 8px">
          <ElButton style="flex: 1" native-type="button" @click="addTodo(true)">再创</ElButton>
          <ElButton type="primary" style="flex: 1" native-type="submit">创建</ElButton>
        </div>
      </ElForm>
    </BaseDialog>

    <!-- 编辑对话框 -->
    <BaseDialog
      v-model="showEdit"
      title="编辑待办"
      width="600px"
      style="max-width: 90vw"
    >
      <ElForm label-position="left" label-width="80px" @submit.prevent="saveEdit">
        <ElFormItem>
          <template #label>
            <span>标题<span style="color: var(--el-color-danger); margin-left: 2px">*</span></span>
          </template>
          <ElInput v-model="editForm.title" placeholder="待办标题" />
        </ElFormItem>
        
        <ElFormItem label="描述">
          <ElInput v-model="editForm.description" type="textarea" :rows="2" placeholder="可选描述" />
        </ElFormItem>

        <ElFormItem label="重要性">
          <ElSlider v-model="editForm.importance" :min="0" :max="100" :marks="importanceMarks" show-stops />
        </ElFormItem>

        <ElFormItem label="紧急性">
          <ElSlider v-model="editForm.urgency" :min="0" :max="100" :marks="urgencyMarks" show-stops />
        </ElFormItem>
        
        <ElFormItem label="时间">
          <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
            <div style="display: flex; gap: 4px; flex: 1; min-width: 200px">
              <ElDatePicker 
                v-model="editForm.start_date" 
                type="date" 
                placeholder="开始日期" 
                clearable 
                style="width: 53%"
                :disabled-date="(date: Date) => disabledStartDate(date, editForm.end_date)"
              />
              <ElTimePicker v-model="editForm.start_time" placeholder="时间" clearable style="width: 47%" />
            </div>
            <span style="font-size: 14px; padding: 0 4px; opacity: 0.7">至</span>
            <div style="display: flex; gap: 4px; flex: 1; min-width: 200px">
              <ElDatePicker 
                v-model="editForm.end_date" 
                type="date" 
                placeholder="截止日期" 
                clearable 
                style="width: 53%"
                :disabled-date="(date: Date) => disabledEndDate(date, editForm.start_date)"
              />
              <ElTimePicker v-model="editForm.end_time" placeholder="时间" clearable style="width: 47%" />
            </div>
          </div>
        </ElFormItem>

        <ElFormItem label="标签">
          <TagInlineInput v-model="editForm.tags" :existing-tags="allExistingTags" placeholder="标签，用逗号分隔" />
          <div v-if="editTodoAvailableTags.length > 0" class="existing-tags">
            <ElTag
              v-for="tag in editTodoAvailableTags"
              :key="tag"
              size="small"
              effect="plain"
              class="existing-tag"
              @click="editForm.tags = addTagToForm(editForm.tags, tag)"
            >
              {{ tag }}
            </ElTag>
          </div>
        </ElFormItem>

        <ElFormItem label="循环">
          <div style="display: flex; gap: 12px; align-items: center; width: 100%">
            <ElSelect v-model="editForm.recurrence_type" :style="{ flex: editForm.recurrence_type === 'custom' ? '0 0 140px' : '1' }">
              <ElOption v-for="item in recurrenceOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
            <div v-if="editForm.recurrence_type === 'custom'" style="display: flex; align-items: center; gap: 8px; flex-shrink: 0">
              <span class="recurrence-text">每</span>
              <ElInputNumber v-model="editForm.recurrence_interval" :min="1" :max="365" style="width: 130px" />
              <span class="recurrence-text">天</span>
            </div>
          </div>
        </ElFormItem>

        <template v-if="editForm.recurrence_type !== 'none'">
          <ElFormItem label="循环次数">
            <div style="display: flex; align-items: center; gap: 12px">
              <ElInputNumber v-model="editForm.recurrence_count" :min="-1" :max="999" />
              <span style="font-size: 12px; opacity: 0.7">-1=无限，0=不循环</span>
            </div>
          </ElFormItem>
          <ElFormItem label="每天完成">
            <div style="display: flex; align-items: center; gap: 12px">
              <ElInputNumber v-model="editForm.times_per_interval" :min="1" :max="999" />
              <span style="font-size: 12px; opacity: 0.7">次</span>
            </div>
          </ElFormItem>
        </template>

        <div style="display: flex; gap: 8px">
          <ElButton type="primary" style="flex: 1" native-type="submit">保存</ElButton>
          <ElButton style="flex: 1" @click="showEdit = false">取消</ElButton>
        </div>
      </ElForm>
    </BaseDialog>
  </div>

  <!-- 重要日专用表单 -->
  <ImportantDayForm
    v-model="showImportantDayForm"
    :editing-todo="editingImportantDay"
    @submit="handleImportantDaySubmit"
  />
</template>

<style scoped>
.todos-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
}

.todos-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.create-button-wrapper {
  display: flex;
}

.status-bar {
  margin-bottom: 16px;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.status-bar-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-button-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-button-group :deep(.el-button) {
  margin-left: 0;
}

.todo-search-input {
  width: min(320px, 100%);
  max-width: 320px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-reset-button {
  padding: 0;
  height: auto;
}

.advanced-filter-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.advanced-filter-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.advanced-filter-label,
.advanced-filter-hint {
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.advanced-filter-actions {
  display: flex;
  justify-content: flex-end;
}

.todo-view-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.todo-view-container--quadrants {
  display: flex;
  overflow: hidden;
}

.multi-select-toolbar {
  position: fixed;
  left: 50%;
  bottom: calc(24px + var(--app-safe-area-bottom));
  transform: translateX(-50%);
  z-index: 1200;
  width: min(920px, calc(100vw - 32px));
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.18);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.multi-select-toolbar__summary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.multi-select-toolbar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.multi-select-danger-button {
  --el-button-bg-color: var(--el-color-danger);
  --el-button-border-color: var(--el-color-danger);
  --el-button-hover-bg-color: var(--el-color-danger-light-3);
  --el-button-hover-border-color: var(--el-color-danger-light-3);
  --el-button-active-bg-color: var(--el-color-danger-dark-2);
  --el-button-active-border-color: var(--el-color-danger-dark-2);
  --el-button-text-color: #fff;
}

.multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button),
.multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button--danger) {
  background-color: var(--el-color-danger) !important;
  border-color: var(--el-color-danger) !important;
  color: #fff !important;
}

.multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button:hover),
.multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button--danger:hover) {
  background-color: var(--el-color-danger-light-3) !important;
  border-color: var(--el-color-danger-light-3) !important;
  color: #fff !important;
}

.multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button:focus-visible),
.multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button--danger:focus-visible) {
  background-color: var(--el-color-danger-light-3) !important;
  border-color: var(--el-color-danger-light-3) !important;
  color: #fff !important;
}

.dark .todo-view-container {
  background: var(--bg-hover);
}

.dark .multi-select-toolbar {
  background: rgba(24, 24, 28, 0.92);
  border-color: rgb(var(--el-color-primary-rgb) / 0.32);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

.dark .multi-select-toolbar__summary {
  color: #fff;
}

.dark .multi-select-danger-button {
  --el-button-bg-color: #f56c6c;
  --el-button-border-color: #f56c6c;
  --el-button-hover-bg-color: #fb8585;
  --el-button-hover-border-color: #fb8585;
  --el-button-active-bg-color: #dd5b5b;
  --el-button-active-border-color: #dd5b5b;
  --el-button-text-color: #fff;
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.16);
}

.dark .multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button),
.dark .multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button--danger) {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: #fff !important;
}

.dark .multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button:hover),
.dark .multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button--danger:hover),
.dark .multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button:focus-visible),
.dark .multi-select-toolbar__actions :deep(.multi-select-danger-button.el-button--danger:focus-visible) {
  background-color: #fb8585 !important;
  border-color: #fb8585 !important;
  color: #fff !important;
}

/* 状态筛选器样式 */
.status-filter-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-filter-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-filter-divider {
  height: 1px;
  background: var(--el-border-color-lighter);
  margin: 6px 8px;
}

.status-filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.status-filter-item:hover {
  background-color: var(--el-fill-color-light);
}

.status-filter-item.is-selected {
  background-color: var(--el-fill-color);
}

.status-filter-text {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.status-count {
  color: var(--el-text-color-secondary);
  font-size: 11px;
  margin-left: auto;
}

/* 深色模式下的筛选器样式 */
.dark .status-filter-item:hover {
  background-color: var(--bg-hover);
}

.dark .status-filter-item.is-selected {
  background-color: rgb(var(--el-color-primary-rgb) / 0.15);
}

.dark .status-filter-text {
  color: var(--text-primary);
}

.dark .status-count {
  color: var(--text-secondary);
}

/* 筛选器 popover 样式覆盖 */
:deep(.status-filter-popover) {
  padding: 8px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid var(--el-border-color-lighter) !important;
}

.dark :deep(.status-filter-popover) {
  background-color: var(--el-bg-color) !important;
  border-color: var(--el-border-color) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

/* 下拉菜单深色模式 */
.dark :deep(.el-select-dropdown) {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.dark :deep(.el-select-dropdown__item) {
  color: var(--el-text-color-regular);
}

.dark :deep(.el-select-dropdown__item.hover),
.dark :deep(.el-select-dropdown__item:hover) {
  background-color: var(--el-fill-color-light);
}

.dark :deep(.el-select-dropdown__item.selected) {
  color: var(--el-color-primary);
}

/* 数字输入器深色模式 */
.dark :deep(.el-input-number) {
  --el-input-bg-color: var(--el-bg-color);
  --el-input-border-color: var(--el-border-color);
  --el-input-text-color: var(--el-text-color-regular);
}

.dark :deep(.el-input-number__decrease),
.dark :deep(.el-input-number__increase) {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color);
  color: var(--el-text-color-regular);
}

.dark :deep(.el-input-number__decrease:hover),
.dark :deep(.el-input-number__increase:hover) {
  color: var(--el-color-primary);
}

/* 滑动条标记文字间距和对齐 */
:deep(.el-slider__marks-text) {
  margin-top: 4px;
}

:deep(.el-slider__marks-text:first-child) {
  transform: translateX(0);
  left: 0 !important;
}

:deep(.el-slider__marks-text:last-child) {
  transform: translateX(0);
  left: auto !important;
  right: 0;
}

/* 循环选择器宽度 */
.recurrence-select-full {
  flex: 1;
  width: 100%;
}

.recurrence-select-short {
  width: 160px;
  flex-shrink: 0;
}

/* 已有标签样式 */
.existing-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.existing-tags-label {
  color: #999;
  font-size: 12px;
}

.existing-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.existing-tag:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.dark .existing-tags-label {
  color: #888;
}

/* 下拉菜单深色模式 - 更全面的覆盖 */
.dark :deep(.el-popper),
.dark :deep(.el-dropdown__popper) {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.dark :deep(.el-select__popper.el-popper) {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.dark :deep(.el-popper__arrow::before) {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

/* 数字输入器深色模式 - 更全面的覆盖 */
.dark :deep(.el-input-number .el-input__wrapper) {
  background-color: var(--el-bg-color);
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}

.dark :deep(.el-input-number .el-input__inner) {
  color: var(--el-text-color-regular);
}

.dark :deep(.el-input-number.is-controls-right .el-input-number__decrease),
.dark :deep(.el-input-number.is-controls-right .el-input-number__increase) {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color);
  color: var(--el-text-color-regular);
}

.dark :deep(.el-input-number.is-controls-right .el-input-number__decrease:hover),
.dark :deep(.el-input-number.is-controls-right .el-input-number__increase:hover) {
  color: var(--el-color-primary);
}

/* 对话框深色模式 */
.dark :deep(.el-dialog) {
  background-color: var(--el-bg-color);
}

.dark :deep(.el-dialog__title) {
  color: var(--el-text-color-primary);
}

.dark :deep(.el-dialog__body) {
  color: var(--el-text-color-regular);
}

.todo-transfer-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.todo-transfer-tip {
  padding: 0;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  font-size: 13px;
}

.todo-transfer-count {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.todo-transfer-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.todo-transfer-options-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.todo-transfer-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.todo-transfer-action {
  height: auto;
  min-height: 132px;
  margin-left: 0;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 10px;
  white-space: normal;
  text-align: left;
}

.todo-transfer-action:hover,
.todo-transfer-action:focus-visible {
  transform: translateY(-1px);
}

.todo-transfer-action-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.todo-transfer-action-content {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.todo-transfer-action-head .el-icon {
  font-size: 16px;
}

.todo-transfer-action-label {
  font-size: 15px;
  font-weight: 600;
}

.todo-transfer-action-desc {
  display: block;
  width: 100%;
  font-size: 12px;
  line-height: 1.6;
  text-align: left;
  color: var(--el-text-color-secondary);
}

.todo-import-input {
  display: none;
}

.dark .todo-transfer-action {
  box-shadow: none;
}

.dark .todo-transfer-action.el-button--primary.is-plain {
  color: var(--el-color-primary-light-5);
  border-color: rgb(var(--el-color-primary-rgb) / 0.4);
  background: rgb(var(--el-color-primary-rgb) / 0.18);
}

.dark .todo-transfer-action.el-button--primary.is-plain:hover,
.dark .todo-transfer-action.el-button--primary.is-plain:focus-visible {
  color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
  background: rgb(var(--el-color-primary-rgb) / 0.28);
}

.dark .todo-transfer-action.el-button--success.is-plain {
  color: #b9e59d;
  border-color: rgba(103, 194, 58, 0.4);
  background: rgba(103, 194, 58, 0.18);
}

.dark .todo-transfer-action.el-button--success.is-plain:hover,
.dark .todo-transfer-action.el-button--success.is-plain:focus-visible {
  color: #def6ce;
  border-color: rgba(149, 212, 117, 0.7);
  background: rgba(103, 194, 58, 0.28);
}

.dark .todo-transfer-action-desc {
  color: rgba(255, 255, 255, 0.72);
}

.dark .todo-transfer-options-label,
.dark .todo-transfer-count {
  color: rgba(255, 255, 255, 0.7);
}

/* 循环文字样式 */
.recurrence-text {
  font-size: 14px;
}

.dark .recurrence-text {
  color: #fff;
}

@media (max-width: 640px) {
  .status-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .todo-search-input {
    width: 100%;
    max-width: none;
  }

  .todo-transfer-actions {
    grid-template-columns: 1fr;
  }

  .multi-select-toolbar {
    width: calc(100vw - 20px);
    bottom: calc(12px + var(--app-safe-area-bottom));
    padding: 12px;
    border-radius: 14px;
    flex-direction: column;
    align-items: stretch;
  }

  .multi-select-toolbar__actions {
    justify-content: stretch;
  }

  .multi-select-toolbar__actions :deep(.el-button) {
    flex: 1 1 calc(50% - 4px);
    min-width: 0;
  }
}
</style>
