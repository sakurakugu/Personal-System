<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, sessionStorage */
import { onMounted, ref, computed } from 'vue'
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
  ElTag,
  ElTimePicker,
} from 'element-plus'
import { List, CircleCheckFilled, WarningFilled, Grid, Menu, Delete, Calendar, Timer, Filter, Star } from '@element-plus/icons-vue'
import { useTodoStore, type Todo, type TodoStatus, type TodoCreateParams, type TodoUpdateParams } from '../../stores/todo'
import BaseDialog from '../../components/BaseDialog.vue'
import TodoCards from './components/TodoCards.vue'
import TodoQuadrants from './components/TodoQuadrants.vue'
import TodoList from './components/TodoList.vue'
import TodoHeatmap from './components/TodoHeatmap.vue'
import TodoGantt from './components/TodoGantt.vue'
import ImportantDays from './components/ImportantDays.vue'
import ImportantDayForm from './components/ImportantDayForm.vue'

const todoStore = useTodoStore()

const showAdd = ref(false)
const showEdit = ref(false)
const editingTodo = ref<Todo | null>(null)
const showRecycleBin = ref(false)
const showImportantDayForm = ref(false)
const editingImportantDay = ref<Todo | null>(null)

// 视图模式：list-列表, cards-卡片瀑布流, quadrants-四象限, heatmap-热力图, gantt-甘特图, important-重要日
type ViewMode = 'list' | 'cards' | 'quadrants' | 'heatmap' | 'gantt' | 'important'
const viewMode = ref<ViewMode>('list')

// 筛选状态
const selectedStatuses = ref<string[]>(['todo', 'done'])


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

// 全选状态（保留供后续使用）
// @ts-expect-error 函数暂时未使用，保留供后续使用
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

const statusGroups = computed(() => ({
  todo: normalTodos.value.filter(t => t.status === 'todo'),

  done: normalTodos.value.filter(t => t.status === 'done'),
}))

// 普通待办列表（排除重要日）
const normalTodos = computed(() => todoStore.todos.filter(t => !isImportantDay(t)))

// 当前显示的待办（多选过滤，按状态分组置顶排序，排除重要日）
const currentTodos = computed(() => {
  if (showRecycleBin.value) {
    return todoStore.deletedTodos
  }
  const filtered = normalTodos.value.filter(t => selectedStatuses.value.includes(t.status))
  return [...filtered].sort((a, b) => {
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
})

// 筛选按钮显示的文本
const filterButtonText = computed(() => {
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
      tags: newTodo.value.tags || undefined,
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
    tags: '重要日',
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
    tags: todo.tags || '',
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
      tags: editForm.value.tags,
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

// 解析标签
function parseTags(tagsStr: string | null): string[] {
  if (!tagsStr) return []
  return tagsStr.split(/[,，]/).map(t => t.trim()).filter(Boolean)
}

// 判断是否为重要日（包含"重要日"标签）
function isImportantDay(todo: Todo): boolean {
  if (!todo.tags) return false
  return parseTags(todo.tags).includes('重要日')
}

// 获取所有已存在的标签（去重，排除"重要日"）
const existingTags = computed(() => {
  const allTags = new Set<string>()
  todoStore.todos.forEach(todo => {
    if (todo.tags) {
      parseTags(todo.tags).forEach(tag => {
        if (tag !== '重要日') {
          allTags.add(tag)
        }
      })
    }
  })
  return Array.from(allTags).sort()
})

// 获取当前表单中未使用的已存在标签
function getAvailableTags(currentTagsStr: string): string[] {
  const currentTags = parseTags(currentTagsStr)
  return existingTags.value.filter(tag => !currentTags.includes(tag))
}

// 添加标签到当前表单
function addTagToForm(formTags: string, tag: string): string {
  const tags = parseTags(formTags)
  if (!tags.includes(tag)) {
    tags.push(tag)
  }
  return tags.join(',')
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
        <span>{{ showRecycleBin ? '回收站' : '待办事项' }}</span>
      </h2>
      <div style="display: flex; gap: 8px">
        <ElButton v-if="showRecycleBin" @click="showRecycleBin = false; todoStore.fetchTodos()">
          返回列表
        </ElButton>
        <ElButton v-if="!showRecycleBin" type="primary" @click="viewMode === 'important' ? openImportantDayForm() : showAdd = true">+ 新建</ElButton>
      </div>
    </div>

    <!-- 状态筛选、视图切换和回收站（仅在非回收站模式显示） -->
    <div v-if="!showRecycleBin" class="status-bar">
      <div class="status-bar-left">
        <ElPopover trigger="click" :width="180" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
          <template #reference>
            <ElButton>
              <span style="display: flex; align-items: center; gap: 6px">
                <ElIcon><Filter /></ElIcon>
                <span>
                  {{ filterButtonText }}
                  ({{ currentTodos.length }})
                </span>
                <span style="margin-left: 4px">▼</span>
              </span>
            </ElButton>
          </template>
          <div class="status-filter-list">
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
            <div class="status-filter-divider" />
            <div class="status-filter-item" @click="openRecycleBin">
              <div class="status-filter-placeholder" />
              <span class="status-filter-text">
                <ElIcon><Delete /></ElIcon>
                <span>回收站</span>
              </span>
            </div>
          </div>
        </ElPopover>
      </div>
      
      <!-- 视图切换按钮 -->
      <ElButtonGroup class="view-toggle">
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
      </ElButtonGroup>
    </div>

    <!-- 列表视图 -->
    <div v-if="viewMode === 'list' || showRecycleBin" class="todo-view-container">
      <TodoList
        :todos="currentTodos"
        :show-recycle-bin="showRecycleBin"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id, mode) => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
      />
    </div>

    <!-- 卡片瀑布流视图 -->
    <div v-else-if="viewMode === 'cards' && !showRecycleBin" class="todo-view-container">
      <TodoCards
        :todos="currentTodos"
        :show-recycle-bin="showRecycleBin"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id, mode) => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
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
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id, mode) => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
      />
      <div v-if="currentTodos.length === 0" class="todo-empty">
        <ElEmpty description="暂无数据" />
      </div>
    </div>

    <!-- 热力图视图 -->
    <div v-else-if="viewMode === 'heatmap' && !showRecycleBin" class="todo-view-container">
      <TodoHeatmap
        :todos="normalTodos"
        @toggle-complete="handleChangeStatusForComponent"
        @edit="openEdit"
      />
    </div>

    <!-- 甘特图视图 -->
    <div v-else-if="viewMode === 'gantt' && !showRecycleBin" class="todo-view-container">
      <TodoGantt
        :todos="currentTodos"
        @edit="openEdit"
        @toggle-pin="handleTogglePin"
        @delete="(id: string, mode: 'soft' | 'permanent') => handleDeleteRequest(id, mode)"
        @restore="handleRestore"
        @change-status="handleChangeStatusForComponent"
      />
    </div>

    <!-- 重要日视图 -->
    <div v-else-if="viewMode === 'important' && !showRecycleBin" class="todo-view-container">
      <ImportantDays
        :todos="todoStore.todos"
        @edit="(todo: Todo) => openImportantDayForm(todo)"
        @toggle-pin="handleTogglePin"
        @delete="(id: string, mode: 'soft' | 'permanent') => handleDeleteRequest(id, mode)"
        @change-status="handleChangeStatusForComponent"
      />
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

    <!-- 新建对话框 -->
    <BaseDialog
      v-model="showAdd"
      :title="newTodo.tags.includes('重要日') ? '新建重要日' : '新建待办'"
      width="560px"
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
                style="width: 60%"
                :disabled-date="(date: Date) => disabledStartDate(date, newTodo.end_date)"
              />
              <ElTimePicker v-model="newTodo.start_time" placeholder="时间" clearable style="width: 40%" />
            </div>
            <span style="font-size: 14px; padding: 0 4px; opacity: 0.7">至</span>
            <div style="display: flex; gap: 4px; flex: 1; min-width: 200px">
              <ElDatePicker 
                v-model="newTodo.end_date" 
                type="date" 
                placeholder="截止日期" 
                clearable 
                style="width: 60%"
                :disabled-date="(date: Date) => disabledEndDate(date, newTodo.start_date)"
              />
              <ElTimePicker v-model="newTodo.end_time" placeholder="时间" clearable style="width: 40%" />
            </div>
          </div>
        </ElFormItem>

        <ElFormItem label="标签">
          <ElInput v-model="newTodo.tags" placeholder="标签，用逗号分隔" />
          <div v-if="getAvailableTags(newTodo.tags).length > 0" class="existing-tags">
            <ElTag
              v-for="tag in getAvailableTags(newTodo.tags)"
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
          <ElFormItem label="每循环完成">
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
                style="width: 60%"
                :disabled-date="(date: Date) => disabledStartDate(date, editForm.end_date)"
              />
              <ElTimePicker v-model="editForm.start_time" placeholder="时间" clearable style="width: 40%" />
            </div>
            <span style="font-size: 14px; padding: 0 4px; opacity: 0.7">至</span>
            <div style="display: flex; gap: 4px; flex: 1; min-width: 200px">
              <ElDatePicker 
                v-model="editForm.end_date" 
                type="date" 
                placeholder="截止日期" 
                clearable 
                style="width: 60%"
                :disabled-date="(date: Date) => disabledEndDate(date, editForm.start_date)"
              />
              <ElTimePicker v-model="editForm.end_time" placeholder="时间" clearable style="width: 40%" />
            </div>
          </div>
        </ElFormItem>

        <ElFormItem label="标签">
          <ElInput v-model="editForm.tags" placeholder="标签，用逗号分隔" />
          <div v-if="getAvailableTags(editForm.tags).length > 0" class="existing-tags">
            <ElTag
              v-for="tag in getAvailableTags(editForm.tags)"
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
          <ElFormItem label="每循环完成">
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

.dark .todo-view-container {
  background: var(--bg-hover);
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

/* 循环文字样式 */
.recurrence-text {
  font-size: 14px;
}

.dark .recurrence-text {
  color: #fff;
}
</style>
