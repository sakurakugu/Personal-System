<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, sessionStorage, clearTimeout, Blob, URL, HTMLInputElement */
import { onBeforeUnmount, onMounted, ref, computed, watch } from 'vue'
import {
  ElButton,
  ElButtonGroup,
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
  ElMessageBox,
} from 'element-plus'
import { List, CircleCheckFilled, WarningFilled, Grid, Menu, Delete, Calendar, Timer, Filter, Star, Download, Upload, Search, ArrowLeft, Select, CloseBold, RefreshRight } from '@element-plus/icons-vue'
import { useTodoStore, type Todo, type TodoStatus, type TodoCreateParams, type TodoUpdateParams, type RecurrenceType } from '../../stores/todo'
import BaseDialog from '../../components/BaseDialog.vue'
import TodoCards from './components/TodoCards.vue'
import TodoQuadrants from './components/TodoQuadrants.vue'
import TodoList from './components/TodoList.vue'
import TodoHeatmap from './components/TodoHeatmap.vue'
import TodoGantt from './components/TodoGantt.vue'
import ImportantDays from './components/ImportantDays.vue'
import ImportantDayForm from './components/ImportantDayForm.vue'
import TagInlineInput from './components/TagInlineInput.vue'
import { getApiErrorMessage } from '../../utils/api'

const todoStore = useTodoStore()

const showAdd = ref(false)
const showEdit = ref(false)
const editingTodo = ref<Todo | null>(null)
const showRecycleBin = ref(false)
const showImportantDayForm = ref(false)
const editingImportantDay = ref<Todo | null>(null)
const showTransferDialog = ref(false)
const isImportingTodos = ref(false)
const todoImportInput = ref<HTMLInputElement | null>(null)
const includeDeletedTodosInExport = ref(false)

let createButtonLongPressTimer: ReturnType<typeof setTimeout> | null = null
let ignoreNextCreateClick = false

const CREATE_BUTTON_LONG_PRESS_MS = 600
const TODO_TRANSFER_VERSION = 1
const VALID_RECURRENCE_TYPES = new Set<RecurrenceType>([
  'none',
  'daily',
  'weekly',
  'monthly',
  'yearly',
  'workday',
  'weekend',
  'holiday',
  'custom',
])

interface TodoTransferItem {
  title: string
  description?: string
  status: TodoStatus
  importance: number
  urgency: number
  start_date?: string
  end_date?: string
  is_pinned: boolean
  tags: string[]
  recurrence_type: RecurrenceType
  recurrence_interval: number
  recurrence_count: number
  times_per_interval: number
  interval_progress: number
  is_deleted: boolean
}

interface TodoTransferPayload {
  version: number
  exported_at: string
  total: number
  todos: TodoTransferItem[]
}

// 视图模式：list-列表, cards-卡片瀑布流, quadrants-四象限, heatmap-热力图, gantt-甘特图, important-重要日
type ViewMode = 'list' | 'cards' | 'quadrants' | 'heatmap' | 'gantt' | 'important'
type PinFilter = 'all' | 'pinned' | 'unpinned'
type RecurrenceFilter = 'all' | 'recurring' | RecurrenceType

const viewMode = ref<ViewMode>('list')

// 筛选状态
const selectedStatuses = ref<string[]>(['todo', 'done'])
const searchKeyword = ref('')
const pinFilter = ref<PinFilter>('all')
const recurrenceFilter = ref<RecurrenceFilter>('all')
const selectedTags = ref<string[]>([])


// 新建表单
const newTodo = ref({
  title: '',
  description: '',
  importance: 33,
  urgency: 33,
  start_date: null as Date | null,
  start_time: null as Date | null,
  end_date: null as Date | null,
  end_time: null as Date | null,
  is_pinned: false,
  tags: '',
  recurrence_type: 'none' as string,
  recurrence_interval: 1,
  recurrence_count: 0,
  times_per_interval: 1,
})

// 编辑表单
const editForm = ref({
  title: '',
  description: '',
  status: 'todo' as TodoStatus,
  importance: 33,
  urgency: 33,
  start_date: null as Date | null,
  start_time: null as Date | null,
  end_date: null as Date | null,
  end_time: null as Date | null,
  is_pinned: false,
  tags: '',
  recurrence_type: 'none' as string,
  recurrence_interval: 1,
  recurrence_count: 0,
  times_per_interval: 1,
})

// 切换状态选择（多选框点击）
function toggleStatus(status: string) {
  const index = selectedStatuses.value.indexOf(status)
  if (index > -1) {
    if (selectedStatuses.value.length > 1) {
      selectedStatuses.value.splice(index, 1)
    }
  } else {
    selectedStatuses.value.push(status)
  }
}

// 单选状态（文字点击）
function selectSingleStatus(status: string) {
  selectedStatuses.value = [status]
}

// 全选状态
function selectAllStatuses() {
  selectedStatuses.value = ['todo', 'done']
}

// 判断是否选中
function isStatusSelected(status: string): boolean {
  return selectedStatuses.value.includes(status)
}

// 删除确认相关
const showDeleteConfirm = ref(false)
const todoToDelete = ref<string | null>(null)
const deleteMode = ref<'soft' | 'permanent'>('soft')
const dontAskAgain = ref(false)
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
  await todoStore.fetchDeletedTodos()
})

watch([viewMode, showRecycleBin], () => {
  exitMultiSelect()
})

function normalizeSearchText(value: string | null | undefined): string {
  return value?.trim().toLowerCase() ?? ''
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
  if (viewMode.value === 'important') {
    return true
  }
  return selectedStatuses.value.includes(todo.status)
}

function sortTodos(todos: Todo[]): Todo[] {
  return [...todos].sort((a, b) => {
    // 先按状态排序：待办在前，已完成在后
    if (a.status !== b.status) {
      return a.status === 'todo' ? -1 : 1
    }
    // 同状态下，置顶优先
    if (a.is_pinned !== b.is_pinned) {
      return a.is_pinned ? -1 : 1
    }
    // 最后按创建时间倒序
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
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

const importantTodos = computed(() => todoStore.todos.filter(isImportantDay))

// 普通待办列表（排除重要日）
const normalTodos = computed(() => todoStore.todos.filter(t => !isImportantDay(t)))

const deletedNormalSourceTodos = computed(() => (
  todoStore.deletedTodos.filter(todo => !isImportantDay(todo))
))

const deletedImportantSourceTodos = computed(() => (
  todoStore.deletedTodos.filter(isImportantDay)
))

const filterSourceTodos = computed(() => {
  if (showRecycleBin.value) {
    return viewMode.value === 'important' ? deletedImportantSourceTodos.value : deletedNormalSourceTodos.value
  }
  return viewMode.value === 'important' ? importantTodos.value : normalTodos.value
})

const filteredSourceTodosBeforeStatus = computed(() => (
  filterSourceTodos.value.filter(todo => matchesAdvancedFilters(todo))
))

const statusGroups = computed(() => ({
  todo: filteredSourceTodosBeforeStatus.value.filter(t => t.status === 'todo'),
  done: filteredSourceTodosBeforeStatus.value.filter(t => t.status === 'done'),
}))

const filteredNormalTodos = computed(() => (
  sortTodos(normalTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
))

const filteredImportantTodos = computed(() => (
  sortTodos(importantTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
))

const filteredDeletedNormalTodos = computed(() => (
  sortTodos(deletedNormalSourceTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
))

const filteredDeletedImportantTodos = computed(() => (
  sortTodos(deletedImportantSourceTodos.value.filter(todo => matchesAdvancedFilters(todo) && matchesStatus(todo)))
))

const isImportantRecycleBinView = computed(() => showRecycleBin.value && viewMode.value === 'important')
const isTodoListViewActive = computed(() => (showRecycleBin.value ? viewMode.value !== 'important' : viewMode.value === 'list'))

// 当前显示的待办数据
const currentTodos = computed(() => {
  if (showRecycleBin.value) {
    return viewMode.value === 'important' ? filteredDeletedImportantTodos.value : filteredDeletedNormalTodos.value
  }
  return filteredNormalTodos.value
})

const multiSelectedIds = ref<string[]>([])

const visibleTodosForMultiSelect = computed(() => {
  if (viewMode.value === 'important') {
    return showRecycleBin.value ? filteredDeletedImportantTodos.value : filteredImportantTodos.value
  }
  if (viewMode.value === 'heatmap') {
    return filteredNormalTodos.value
  }
  return currentTodos.value
})

const visibleTodoIdSet = computed(() => new Set(visibleTodosForMultiSelect.value.map(todo => todo.id)))
const selectedTodoIdSet = computed(() => new Set(multiSelectedIds.value))
const isMultiSelectMode = ref(false)
const selectedTodos = computed(() => {
  const todoMap = new Map([...todoStore.todos, ...todoStore.deletedTodos].map(todo => [todo.id, todo]))
  return multiSelectedIds.value
    .map(id => todoMap.get(id))
    .filter((todo): todo is Todo => Boolean(todo))
})
const selectedVisibleTodos = computed(() => (
  visibleTodosForMultiSelect.value.filter(todo => selectedTodoIdSet.value.has(todo.id))
))
const allVisibleSelected = computed(() => (
  visibleTodosForMultiSelect.value.length > 0
  && selectedVisibleTodos.value.length === visibleTodosForMultiSelect.value.length
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

const visibleTodoCount = computed(() => {
  if (showRecycleBin.value) {
    return currentTodos.value.length
  }
  return viewMode.value === 'important' ? filteredImportantTodos.value.length : filteredNormalTodos.value.length
})

const hasSearchKeyword = computed(() => Boolean(searchKeyword.value.trim()))

const extraFilterCount = computed(() => {
  return Number(pinFilter.value !== 'all')
    + Number(recurrenceFilter.value !== 'all')
    + Number(selectedTags.value.length > 0)
})

const hasAnyFilters = computed(() => {
  return hasSearchKeyword.value || extraFilterCount.value > 0 || (viewMode.value !== 'important' && selectedStatuses.value.length !== 2)
})

// 筛选按钮显示的文本
const filterButtonText = computed(() => {
  if (viewMode.value === 'important') {
    return '全部'
  }
  if (selectedStatuses.value.length === 2) {
    return '全部'
  }
  // 按固定顺序显示选中的状态
  const order = ['todo', 'done']
  const selected = order.filter(s => selectedStatuses.value.includes(s))
  return selected.map(s => statusLabel[s]).join('/') || '请选择'
})



const statusLabel: Record<string, string> = {
  todo: '待办',

  done: '已完成',
}

const statusIcon = {
  todo: List,

  done: CircleCheckFilled,
}

const statusOrder: Record<string, string> = {
  todo: 'done',
  done: 'todo',
}

const nextStatusLabel: Record<string, string> = {
  todo: '设为完成',
  done: '重设为待办',
}

const pinFilterLabel: Record<PinFilter, string> = {
  all: '全部',
  pinned: '仅置顶',
  unpinned: '未置顶',
}

const recurrenceOptions = [
  { label: '不循环', value: 'none' },
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' },
  { label: '每年', value: 'yearly' },
  { label: '工作日', value: 'workday' },
  { label: '周末', value: 'weekend' },
  { label: '节假日', value: 'holiday' },
  { label: '自定义', value: 'custom' },
]

const recurrenceFilterLabel = computed(() => {
  if (recurrenceFilter.value === 'all') {
    return '全部'
  }
  if (recurrenceFilter.value === 'recurring') {
    return '仅循环'
  }
  return recurrenceOptions.find(item => item.value === recurrenceFilter.value)?.label ?? '未知'
})

const importanceMarks = { 0: '不重要', 33: '一般', 66: '重要', 100: '非常重要' }
const urgencyMarks = { 0: '不紧急', 33: '一般', 66: '紧急', 100: '非常紧急' }

// 组合日期和时间
function combineDateTime(date: Date | null, time: Date | null): string | undefined {
  if (!date) return undefined
  const d = new Date(date)
  if (time) {
    const t = new Date(time)
    d.setHours(t.getHours(), t.getMinutes(), 0, 0)
  }
  return d.toISOString()
}

// 拆分日期时间
function splitDateTime(isoString: string | null): { date: Date | null, time: Date | null } {
  if (!isoString) return { date: null, time: null }
  const d = new Date(isoString)
  const date = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const time = new Date(2000, 0, 1, d.getHours(), d.getMinutes())
  return { date, time }
}

function parseTagsInput(tagsText: string): string[] {
  return tagsText.split(/[,，]/).map(tag => tag.trim()).filter(Boolean)
}

function formatTagsInput(tags: string[] | null): string {
  if (!tags) return ''
  return tags.join(',')
}

async function addTodo() {
  if (!newTodo.value.title.trim()) return
  try {
    await todoStore.addTodo({
      title: newTodo.value.title,
      description: newTodo.value.description || undefined,
      importance: newTodo.value.importance,
      urgency: newTodo.value.urgency,
      start_date: combineDateTime(newTodo.value.start_date, newTodo.value.start_time),
      end_date: combineDateTime(newTodo.value.end_date, newTodo.value.end_time),
      is_pinned: newTodo.value.is_pinned,
      tags: parseTagsInput(newTodo.value.tags),
      recurrence_type: newTodo.value.recurrence_type as any,
      recurrence_interval: newTodo.value.recurrence_interval,
      recurrence_count: newTodo.value.recurrence_count,
      times_per_interval: newTodo.value.times_per_interval,
    })
    showAdd.value = false
    resetNewTodo()
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
  newTodo.value = {
    title: '',
    description: '',
    importance: 33,
    urgency: 33,
    start_date: null,
    start_time: null,
    end_date: null,
    end_time: null,
    is_pinned: false,
    tags: '',
    recurrence_type: 'none',
    recurrence_interval: 1,
    recurrence_count: 0,
    times_per_interval: 1,
  }
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
    // 刷新列表
    await todoStore.fetchTodos()
    showImportantDayForm.value = false
    editingImportantDay.value = null
  } catch {
    ElMessage.error(editingImportantDay.value ? '保存失败' : '创建失败')
  }
}

function openEdit(todo: Todo) {
  editingTodo.value = todo
  const start = splitDateTime(todo.start_date)
  const end = splitDateTime(todo.end_date)
  editForm.value = {
    title: todo.title,
    description: todo.description || '',
    status: todo.status,
    importance: todo.importance,
    urgency: todo.urgency,
    start_date: start.date,
    start_time: start.time,
    end_date: end.date,
    end_time: end.time,
    is_pinned: todo.is_pinned,
    tags: formatTagsInput(todo.tags),
    recurrence_type: todo.recurrence_type,
    recurrence_interval: todo.recurrence_interval,
    recurrence_count: todo.recurrence_count,
    times_per_interval: todo.times_per_interval,
  }
  showEdit.value = true
}

async function saveEdit() {
  if (!editingTodo.value || !editForm.value.title.trim()) return
  try {
    await todoStore.updateTodo(editingTodo.value.id, {
      title: editForm.value.title,
      description: editForm.value.description || undefined,
      status: editForm.value.status,
      importance: editForm.value.importance,
      urgency: editForm.value.urgency,
      start_date: combineDateTime(editForm.value.start_date, editForm.value.start_time),
      end_date: combineDateTime(editForm.value.end_date, editForm.value.end_time),
      is_pinned: editForm.value.is_pinned,
      tags: parseTagsInput(editForm.value.tags),
      recurrence_type: editForm.value.recurrence_type as any,
      recurrence_interval: editForm.value.recurrence_interval,
      recurrence_count: editForm.value.recurrence_count,
      times_per_interval: editForm.value.times_per_interval,
    })
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
    await todoStore.updateTodo(todo.id, { status: newStatus, interval_progress: 0 })
  }
}

async function handleTogglePin(todo: Todo) {
  await todoStore.togglePin(todo.id)
}

function handleDeleteRequest(id: string, mode: 'soft' | 'permanent' = 'soft') {
  todoToDelete.value = id
  deleteMode.value = mode
  if (shouldSkipConfirm()) {
    confirmDelete()
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
      await todoStore.permanentlyDeleteTodo(todoToDelete.value)
      ElMessage.success('已永久删除')
    } else {
      await todoStore.deleteTodo(todoToDelete.value)
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

async function handleRestore(id: string) {
  try {
    await todoStore.restoreTodo(id)
    ElMessage.success('已恢复')
  } catch {
    ElMessage.error('恢复失败')
  }
}

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
  multiSelectedIds.value = visibleTodosForMultiSelect.value.map(todo => todo.id)
}

async function batchChangeSelectedStatus() {
  const targetStatus: TodoStatus = hasSelectedTodoNeedingDone.value ? 'done' : 'todo'
  const targetTodos = selectedTodos.value.filter(todo => todo.status !== targetStatus)
  const count = targetTodos.length
  if (targetTodos.length === 0) {
    exitMultiSelect()
    return
  }

  try {
    await Promise.all(targetTodos.map(todo => changeStatus(todo, targetStatus)))
    ElMessage.success(`已批量${targetStatus === 'done' ? '完成' : '重置为待办'} ${count} 项`)
    exitMultiSelect()
  } catch {
    ElMessage.error('批量修改状态失败')
  }
}

async function batchTogglePinSelectedTodos() {
  const todos = [...selectedTodos.value]
  const count = todos.length
  if (count === 0) return

  const nextPinned = hasSelectedTodoNeedingPin.value
  const targetTodos = todos.filter(todo => todo.is_pinned !== nextPinned)
  if (targetTodos.length === 0) {
    exitMultiSelect()
    return
  }

  try {
    await Promise.all(targetTodos.map(todo => todoStore.updateTodo(todo.id, { is_pinned: nextPinned })))
    ElMessage.success(`已批量${nextPinned ? '置顶' : '取消置顶'} ${targetTodos.length} 项`)
    exitMultiSelect()
  } catch {
    ElMessage.error('批量置顶失败')
  }
}

async function batchDeleteSelectedTodos() {
  const todos = [...selectedTodos.value]
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
    await Promise.all(todos.map(todo => todoStore.deleteTodo(todo.id)))
    ElMessage.success(`已移至回收站 ${count} 项`)
    exitMultiSelect()
  } catch {
    ElMessage.error('批量删除失败')
  }
}

async function batchRestoreSelectedTodos() {
  const todos = [...selectedTodos.value]
  const count = todos.length
  if (count === 0) return
  try {
    await Promise.all(todos.map(todo => todoStore.restoreTodo(todo.id)))
    ElMessage.success(`已恢复 ${count} 项`)
    exitMultiSelect()
  } catch {
    ElMessage.error('批量恢复失败')
  }
}

async function batchPermanentDeleteSelectedTodos() {
  const todos = [...selectedTodos.value]
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
    await Promise.all(todos.map(todo => todoStore.permanentlyDeleteTodo(todo.id)))
    ElMessage.success(`已永久删除 ${count} 项`)
    exitMultiSelect()
  } catch {
    ElMessage.error('批量永久删除失败')
  }
}

// 处理组件中的状态变更
async function handleChangeStatusForComponent(todo: Todo) {
  const nextStatus = statusOrder[todo.status] as TodoStatus
  await changeStatus(todo, nextStatus)
  ElMessage.success(`${todo.title} 已${nextStatusLabel[todo.status]}`)
}

// 打开回收站
async function openRecycleBin() {
  showRecycleBin.value = true
  await todoStore.fetchDeletedTodos()
}

// 关闭回收站
async function closeRecycleBin() {
  showRecycleBin.value = false
  await todoStore.fetchTodos()
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

// 判断是否为重要日（包含"重要日"标签）
function isImportantDay(todo: Todo): boolean {
  if (!todo.tags) return false
  return todo.tags.includes('重要日')
}

// 获取所有已存在的标签（去重）
const allExistingTags = computed(() => {
  const allTags = new Set<string>()
  todoStore.todos.forEach(todo => {
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

function normalizeTodoStatus(value: unknown): TodoStatus {
  return value === 'done' ? 'done' : 'todo'
}

function normalizeRecurrenceType(value: unknown): RecurrenceType {
  if (typeof value === 'string' && VALID_RECURRENCE_TYPES.has(value as RecurrenceType)) {
    return value as RecurrenceType
  }
  return 'none'
}

function normalizeNumber(value: unknown, fallback: number, options?: { min?: number; max?: number }): number {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return fallback
  }
  const min = options?.min ?? Number.NEGATIVE_INFINITY
  const max = options?.max ?? Number.POSITIVE_INFINITY
  return Math.min(max, Math.max(min, Math.round(value)))
}

function normalizeOptionalDate(value: unknown): string | undefined {
  if (typeof value !== 'string' || !value.trim()) {
    return undefined
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return undefined
  }
  return date.toISOString()
}

function normalizeTags(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .filter((tag): tag is string => typeof tag === 'string')
    .map(tag => tag.trim())
    .filter(Boolean)
}

function normalizeTodoTransferItem(item: unknown): TodoTransferItem | null {
  if (!item || typeof item !== 'object') {
    return null
  }
  const record = item as Record<string, unknown>
  const title = typeof record.title === 'string' ? record.title.trim() : ''
  if (!title) {
    return null
  }

  const recurrenceType = normalizeRecurrenceType(record.recurrence_type)
  const timesPerInterval = normalizeNumber(record.times_per_interval, 1, { min: 1, max: 999 })

  return {
    title,
    description: typeof record.description === 'string' && record.description.trim() ? record.description.trim() : undefined,
    status: normalizeTodoStatus(record.status),
    importance: normalizeNumber(record.importance, 33, { min: 0, max: 100 }),
    urgency: normalizeNumber(record.urgency, 33, { min: 0, max: 100 }),
    start_date: normalizeOptionalDate(record.start_date),
    end_date: normalizeOptionalDate(record.end_date),
    is_pinned: Boolean(record.is_pinned),
    tags: normalizeTags(record.tags),
    recurrence_type: recurrenceType,
    recurrence_interval: normalizeNumber(record.recurrence_interval, 1, { min: 1, max: 365 }),
    recurrence_count: recurrenceType === 'none'
      ? 0
      : normalizeNumber(record.recurrence_count, 0, { min: -1, max: 999 }),
    times_per_interval: recurrenceType === 'none' ? 1 : timesPerInterval,
    interval_progress: recurrenceType === 'none'
      ? 0
      : normalizeNumber(record.interval_progress, 0, { min: 0, max: timesPerInterval }),
    is_deleted: Boolean(record.is_deleted),
  }
}

function parseTodoTransferPayload(rawText: string): TodoTransferItem[] {
  const parsed = JSON.parse(rawText) as unknown
  const items = Array.isArray(parsed)
    ? parsed
    : parsed && typeof parsed === 'object' && Array.isArray((parsed as { todos?: unknown }).todos)
      ? (parsed as { todos: unknown[] }).todos
      : null

  if (!items) {
    throw new Error('导入文件格式不正确')
  }

  const normalized = items
    .map(item => normalizeTodoTransferItem(item))
    .filter((item): item is TodoTransferItem => item !== null)

  if (normalized.length === 0) {
    throw new Error('导入文件中没有可用的待办事项')
  }

  return normalized
}

function toTodoTransferItem(todo: Todo): TodoTransferItem {
  return {
    title: todo.title,
    description: todo.description ?? undefined,
    status: todo.status,
    importance: todo.importance,
    urgency: todo.urgency,
    start_date: todo.start_date ?? undefined,
    end_date: todo.end_date ?? undefined,
    is_pinned: todo.is_pinned,
    tags: todo.tags ?? [],
    recurrence_type: todo.recurrence_type,
    recurrence_interval: todo.recurrence_interval,
    recurrence_count: todo.recurrence_count,
    times_per_interval: todo.times_per_interval,
    interval_progress: todo.interval_progress,
    is_deleted: todo.is_deleted,
  }
}

function normalizeFingerprintDate(value: string | undefined): string {
  return normalizeOptionalDate(value) || ''
}

function getTodoTransferFingerprint(todo: TodoTransferItem): string {
  return JSON.stringify({
    title: todo.title.trim(),
    description: todo.description?.trim() || '',
    status: todo.status,
    importance: todo.importance,
    urgency: todo.urgency,
    start_date: normalizeFingerprintDate(todo.start_date),
    end_date: normalizeFingerprintDate(todo.end_date),
    is_pinned: todo.is_pinned,
    tags: Array.from(new Set(todo.tags.map(tag => tag.trim()).filter(Boolean))).sort(),
    recurrence_type: todo.recurrence_type,
    recurrence_interval: todo.recurrence_interval,
    recurrence_count: todo.recurrence_count,
    times_per_interval: todo.times_per_interval,
    interval_progress: todo.interval_progress,
    is_deleted: todo.is_deleted,
  })
}

function getTodoFingerprint(todo: Todo): string {
  return getTodoTransferFingerprint(toTodoTransferItem(todo))
}

const exportTodoTotal = computed(() => (
  todoStore.todos.length + (includeDeletedTodosInExport.value ? todoStore.deletedTodos.length : 0)
))

async function exportTodos() {
  if (includeDeletedTodosInExport.value) {
    await todoStore.fetchDeletedTodos()
  }

  const todosToExport = includeDeletedTodosInExport.value
    ? [...todoStore.todos, ...todoStore.deletedTodos]
    : todoStore.todos

  const payload: TodoTransferPayload = {
    version: TODO_TRANSFER_VERSION,
    exported_at: new Date().toISOString(),
    total: todosToExport.length,
    todos: todosToExport.map(todo => toTodoTransferItem(todo)),
  }
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
  todoImportInput.value?.click()
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
    if (hasDeletedItems) {
      await todoStore.fetchDeletedTodos()
    }
    const existingFingerprints = new Set([
      ...todoStore.todos.map(todo => getTodoFingerprint(todo)),
      ...todoStore.deletedTodos.map(todo => getTodoFingerprint(todo)),
    ])

    for (const [index, item] of todosToImport.entries()) {
      const fingerprint = getTodoTransferFingerprint(item)
      if (existingFingerprints.has(fingerprint)) {
        mergedCount += 1
        continue
      }

      try {
        const created = await todoStore.addTodo({
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
          await todoStore.updateTodo(created.id, {
            status: item.status,
            interval_progress: item.interval_progress,
          })
        }
        if (item.is_deleted) {
          await todoStore.deleteTodo(created.id)
        }

        existingFingerprints.add(fingerprint)
        importedCount += 1
      } catch (error) {
        throw new Error(`第 ${index + 1} 条导入失败：${getApiErrorMessage(error, '请检查待办字段')}`, { cause: error })
      }
    }

    await todoStore.fetchTodos()
    await todoStore.fetchDeletedTodos()
    showTransferDialog.value = false
    ElMessage.success(
      mergedCount > 0
        ? `已导入 ${importedCount} 条，合并 ${mergedCount} 条重复待办`
        : `已导入 ${importedCount} 条待办`,
    )
  } catch (error) {
    if (importedCount > 0) {
      await todoStore.fetchTodos()
      await todoStore.fetchDeletedTodos()
    }
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

// 获取四象限分类（后续使用）
// @ts-expect-error 函数暂时未使用，保留供后续功能使用
function getQuadrant(importance: number, urgency: number): string {
  if (importance >= 50 && urgency >= 50) return '重要且紧急'
  if (importance >= 50) return '重要不紧急'
  if (urgency >= 50) return '不重要紧急'
  return '不重要不紧急'
}
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
                <div class="status-filter-placeholder" />
                <span
                  class="status-filter-text"
                >
                  <ElIcon><List /></ElIcon>
                  <span>全部</span>
                  <span class="status-count">({{ visibleTodoCount }})</span>
                </span>
              </div>
              <template v-else>
                <div
                  v-for="key in ['todo', 'done']"
                  :key="key"
                  class="status-filter-item"
                  :class="{ 'is-selected': isStatusSelected(key) }"
                >
                  <ElCheckbox
                    :model-value="isStatusSelected(key)"
                    @change="toggleStatus(key)"
                  />
                  <span
                    class="status-filter-text"
                    @click="selectSingleStatus(key)"
                  >
                    <ElIcon><component :is="statusIcon[key as keyof typeof statusIcon]" /></ElIcon>
                    <span>{{ statusLabel[key] }}</span>
                    <span class="status-count">({{ statusGroups[key as keyof typeof statusGroups].length }})</span>
                  </span>
                </div>
              </template>
              <template v-if="!showRecycleBin">
                <div class="status-filter-divider" />
                <div class="status-filter-item" @click="openRecycleBin">
                  <div class="status-filter-placeholder" />
                  <span class="status-filter-text">
                    <ElIcon><Delete /></ElIcon>
                    <span>回收站</span>
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="status-filter-divider" />
                <div class="status-filter-item" @click="closeRecycleBin">
                  <div class="status-filter-placeholder" />
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
      <ElButtonGroup class="view-toggle">
        <template v-if="showRecycleBin">
          <ElButton
            :type="isTodoListViewActive ? 'primary' : ''"
            title="待办列表"
            @click="viewMode = 'list'"
          >
            <span style="display: flex; align-items: center; gap: 6px">
              <ElIcon><List /></ElIcon>
              <span>待办列表</span>
            </span>
          </ElButton>
          <ElButton
            :type="viewMode === 'important' ? 'primary' : ''"
            title="重要日"
            @click="viewMode = 'important'"
          >
            <span style="display: flex; align-items: center; gap: 6px">
              <ElIcon><Star /></ElIcon>
              <span>重要日</span>
            </span>
          </ElButton>
        </template>
        <template v-else>
          <ElButton
            :type="viewMode === 'list' ? 'primary' : ''"
            title="列表视图"
            @click="viewMode = 'list'"
          >
            <ElIcon><List /></ElIcon>
          </ElButton>
          <ElButton
            :type="viewMode === 'cards' ? 'primary' : ''"
            title="卡片视图"
            @click="viewMode = 'cards'"
          >
            <ElIcon><Grid /></ElIcon>
          </ElButton>
          <ElButton
            :type="viewMode === 'quadrants' ? 'primary' : ''"
            title="四象限视图"
            @click="viewMode = 'quadrants'"
          >
            <ElIcon><Menu /></ElIcon>
          </ElButton>
          <ElButton
            :type="viewMode === 'heatmap' ? 'primary' : ''"
            title="热力图视图"
            @click="viewMode = 'heatmap'"
          >
            <ElIcon><Calendar /></ElIcon>
          </ElButton>
          <ElButton
            :type="viewMode === 'gantt' ? 'primary' : ''"
            title="时间条视图"
            @click="viewMode = 'gantt'"
          >
            <ElIcon><Timer /></ElIcon>
          </ElButton>
          <ElButton
            :type="viewMode === 'important' ? 'primary' : ''"
            title="重要日"
            @click="viewMode = 'important'"
          >
            <ElIcon><Star /></ElIcon>
          </ElButton>
        </template>
      </ElButtonGroup>
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
    <div v-else-if="viewMode === 'quadrants' && !showRecycleBin" class="todo-view-container">
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
      <div v-if="currentTodos.length === 0" class="todo-empty">
        <ElEmpty description="暂无数据" />
      </div>
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
      @closed="resetNewTodo"
    >
      <ElForm label-position="left" label-width="80px" @submit.prevent="addTodo">
        <ElFormItem>
          <template #label>
            <span>标题<span style="color: var(--el-color-danger); margin-left: 2px">*</span></span>
          </template>
          <ElInput v-model="newTodo.title" placeholder="待办标题" />
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

        <ElButton type="primary" style="width: 100%" native-type="submit">创建</ElButton>
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

.view-toggle {
  display: flex;
}

.view-toggle :deep(.el-button) {
  padding: 8px 12px;
}

.todo-view-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.multi-select-toolbar {
  position: fixed;
  left: 50%;
  bottom: 24px;
  transform: translateX(-50%);
  z-index: 1200;
  width: min(920px, calc(100vw - 32px));
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  border: 1px solid rgba(64, 158, 255, 0.18);
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
  border-color: rgba(64, 158, 255, 0.32);
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
  cursor: pointer;
  color: var(--el-text-color-primary);
}

/* 占位元素，用于回收站项对齐 checkbox 位置 */
.status-filter-placeholder {
  width: 14px;
  flex-shrink: 0;
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
  background-color: rgba(24, 160, 88, 0.15);
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
  color: #a9d4ff;
  border-color: rgba(64, 158, 255, 0.4);
  background: rgba(64, 158, 255, 0.18);
}

.dark .todo-transfer-action.el-button--primary.is-plain:hover,
.dark .todo-transfer-action.el-button--primary.is-plain:focus-visible {
  color: #d7ebff;
  border-color: rgba(121, 187, 255, 0.7);
  background: rgba(64, 158, 255, 0.28);
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

  .view-toggle {
    width: 100%;
  }

  .view-toggle :deep(.el-button) {
    flex: 1;
  }

  .todo-transfer-actions {
    grid-template-columns: 1fr;
  }

  .multi-select-toolbar {
    width: calc(100vw - 20px);
    bottom: 12px;
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
