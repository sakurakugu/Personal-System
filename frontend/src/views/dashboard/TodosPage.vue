<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, sessionStorage */
import { onMounted, ref, computed, reactive } from 'vue'
import {
  ElButton,
  ElCard,
  ElCheckbox,
  ElDatePicker,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElPopover,
  ElSelect,
  ElSlider,
  ElTag,
  ElTimePicker,
} from 'element-plus'
import { List, RefreshRight, CircleCheckFilled, Delete, Check, Clock, WarningFilled, Star } from '@element-plus/icons-vue'
import { useTodoStore, type Todo, type TodoStatus } from '../../stores/todo'

const todoStore = useTodoStore()

const showAdd = ref(false)
const showEdit = ref(false)
const editingTodo = ref<Todo | null>(null)
const showRecycleBin = ref(false)

// 筛选状态
const selectedStatuses = ref<string[]>(['todo', 'in_progress'])


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
  selectedStatuses.value = ['todo', 'in_progress', 'done']
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

// 滑动相关状态
const swipeState = reactive<Record<string, {
  offset: number
  startX: number
  startY: number
  isDragging: boolean
  hasMoved: boolean
}>>({})

const SWIPE_THRESHOLD = 80
const MAX_OFFSET = 120

onMounted(() => {
  todoStore.fetchTodos()
})

const statusGroups = computed(() => ({
  todo: todoStore.todos.filter(t => t.status === 'todo'),
  in_progress: todoStore.todos.filter(t => t.status === 'in_progress'),
  done: todoStore.todos.filter(t => t.status === 'done'),
}))

// 当前显示的待办（多选过滤）
const currentTodos = computed(() => {
  if (showRecycleBin.value) {
    return todoStore.deletedTodos
  }
  return todoStore.todos.filter(t => selectedStatuses.value.includes(t.status))
})

// 筛选按钮显示的文本
const filterButtonText = computed(() => {
  if (selectedStatuses.value.length === 3) {
    return '全部'
  }
  // 按固定顺序显示选中的状态
  const order = ['todo', 'in_progress', 'done']
  const selected = order.filter(s => selectedStatuses.value.includes(s))
  return selected.map(s => statusLabel[s]).join('/') || '请选择'
})



const statusLabel: Record<string, string> = {
  todo: '待办',
  in_progress: '进行中',
  done: '已完成',
}

const statusIcon = {
  todo: List,
  in_progress: RefreshRight,
  done: CircleCheckFilled,
}

const statusOrder: Record<string, string> = {
  todo: 'in_progress',
  in_progress: 'done',
  done: 'todo',
}

const nextStatusLabel: Record<string, string> = {
  todo: '设为进行中',
  in_progress: '设为完成',
  done: '重设为待办',
}

const nextStatusIcon: Record<string, any> = {
  todo: RefreshRight,
  in_progress: Check,
  done: Clock,
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
      tags: editForm.value.tags || undefined,
      recurrence_type: editForm.value.recurrence_type as any,
      recurrence_interval: editForm.value.recurrence_interval,
      recurrence_count: editForm.value.recurrence_count,
    })
    showEdit.value = false
    editingTodo.value = null
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  }
}

async function changeStatus(todo: Todo, newStatus: TodoStatus) {
  await todoStore.updateTodo(todo.id, { status: newStatus })
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

// 打开回收站
async function openRecycleBin() {
  showRecycleBin.value = true
  await todoStore.fetchDeletedTodos()
}

// 滑动事件处理
function initSwipeState(id: string) {
  if (!swipeState[id]) {
    swipeState[id] = { offset: 0, startX: 0, startY: 0, isDragging: false, hasMoved: false }
  }
}

function onTouchStart(e: Event, id: string) {
  initSwipeState(id)
  const state = swipeState[id]
  state.isDragging = true
  
  if (e instanceof TouchEvent) {
    state.startX = e.touches[0].clientX
    state.startY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    state.startX = e.clientX
    state.startY = e.clientY
  }
}

function onTouchMove(e: Event, id: string) {
  const state = swipeState[id]
  if (!state?.isDragging) return

  let clientX = 0
  let clientY = 0
  if (e instanceof TouchEvent) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else if (e instanceof MouseEvent) {
    clientX = e.clientX
    clientY = e.clientY
  }

  const deltaX = clientX - state.startX
  const deltaY = clientY - state.startY

  if (Math.abs(deltaY) > Math.abs(deltaX)) return

  // 标记为已滑动（移动超过 5px 视为滑动而非点击）
  if (Math.abs(deltaX) > 5) {
    state.hasMoved = true
  }

  if (e instanceof TouchEvent && Math.abs(deltaX) > 10) {
    e.preventDefault()
  }

  state.offset = Math.max(-MAX_OFFSET, Math.min(MAX_OFFSET, deltaX))
}

function onTouchEnd(id: string) {
  const state = swipeState[id]
  if (!state) return

  // 延迟重置 hasMoved，防止 click 事件立即触发
  const hadMoved = state.hasMoved
  state.isDragging = false
  
  // 如果发生了滑动，延迟重置 hasMoved，确保 click 事件能检测到这个标志
  if (hadMoved) {
    setTimeout(() => {
      state.hasMoved = false
    }, 50)
  } else {
    state.hasMoved = false
  }

  const todo = currentTodos.value.find(t => t.id === id)
  if (!todo) {
    state.offset = 0
    return
  }

  // 回收站模式：左滑永久删除，右滑恢复
  if (showRecycleBin.value) {
    // 向左滑动：永久删除
    if (state.offset < -SWIPE_THRESHOLD) {
      handleDeleteRequest(id, 'permanent')
      state.offset = 0
      return
    }

    // 向右滑动：恢复
    if (state.offset > SWIPE_THRESHOLD) {
      handleRestore(id)
      state.offset = 0
      return
    }
  } else {
    // 正常模式：左滑删除，右滑切换状态
    // 向左滑动：删除
    if (state.offset < -SWIPE_THRESHOLD) {
      handleDeleteRequest(id, 'soft')
      state.offset = 0
      return
    }

    // 向右滑动：切换状态
    if (state.offset > SWIPE_THRESHOLD) {
      const nextStatus = statusOrder[todo.status] as TodoStatus
      changeStatus(todo, nextStatus)
      ElMessage.success(`${todo.title} 已${nextStatusLabel[todo.status]}`)
      state.offset = 0
      return
    }
  }

  state.offset = 0
}

// 处理卡片点击事件（区分滑动和点击）
function handleCardClick(todo: Todo) {
  const state = swipeState[todo.id]
  if (state?.hasMoved) {
    // 如果发生了滑动，不触发点击
    return
  }
  if (!showRecycleBin.value && todo.status !== 'done') {
    openEdit(todo)
  }
}

// 检查是否接近截止日期（24小时内）
function isNearDeadline(endDate: string | null): boolean {
  if (!endDate) return false
  const end = new Date(endDate)
  const now = new Date()
  const diff = end.getTime() - now.getTime()
  // 小于24小时且未过期
  return diff > 0 && diff < 24 * 60 * 60 * 1000
}

// 检查是否已过期
function isOverdue(endDate: string | null): boolean {
  if (!endDate) return false
  const end = new Date(endDate)
  const now = new Date()
  return end.getTime() < now.getTime()
}

// 获取优先级标签类型
// 0-32: info(灰色-不重要), 33-66: success(绿色-一般), 67-85: warning(黄色-重要), 86-100: danger(红色-非常重要)
function getPriorityTagType(value: number): 'success' | 'info' | 'warning' | 'danger' {
  if (value >= 86) return 'danger'
  if (value >= 67) return 'warning'
  if (value >= 33) return 'success'
  return 'info'
}

// 获取优先级标签文字
function getPriorityLabel(value: number): string {
  if (value >= 86) return '非常重要'
  if (value >= 67) return '重要'
  if (value >= 33) return '一般'
  return '不重要'
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

function getCardStyle(id: string) {
  const state = swipeState[id]
  if (!state) return {}
  return {
    transform: `translateX(${state.offset}px)`,
    transition: state.isDragging ? 'none' : 'transform 0.3s ease',
  }
}

function getLeftActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }
  const opacity = Math.min(1, Math.max(0, state.offset / SWIPE_THRESHOLD))
  return {
    opacity: opacity,
    transform: `scale(${0.8 + opacity * 0.2})`,
  }
}

function getRightActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }
  const opacity = Math.min(1, Math.max(0, -state.offset / SWIPE_THRESHOLD))
  return {
    opacity: opacity,
    transform: `scale(${0.8 + opacity * 0.2})`,
  }
}

// 解析标签
function parseTags(tagsStr: string | null): string[] {
  if (!tagsStr) return []
  return tagsStr.split(/[,，]/).map(t => t.trim()).filter(Boolean)
}

// 获取所有已存在的标签（去重）
const existingTags = computed(() => {
  const allTags = new Set<string>()
  todoStore.todos.forEach(todo => {
    if (todo.tags) {
      parseTags(todo.tags).forEach(tag => allTags.add(tag))
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

// 格式化日期时间显示
function formatDateTime(isoString: string | null): string {
  if (!isoString) return ''
  const d = new Date(isoString)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
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
        <ElButton v-if="!showRecycleBin" type="primary" @click="showAdd = true">+ 新建</ElButton>
      </div>
    </div>

    <!-- 状态筛选和回收站（仅在非回收站模式显示） -->
    <div v-if="!showRecycleBin" class="status-bar">
      <ElPopover trigger="click" :width="180" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
        <template #reference>
          <ElButton>
            <span style="display: flex; align-items: center; gap: 6px">
              <ElIcon><List /></ElIcon>
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
            v-for="key in ['todo', 'in_progress', 'done']"
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
            <span class="status-filter-text" style="padding-left: 28px">
              <ElIcon><Delete /></ElIcon>
              <span>回收站</span>
            </span>
          </div>
        </div>
      </ElPopover>
    </div>

    <div class="todo-list">
      <div
        v-for="t in currentTodos"
        :key="t.id"
        class="todo-swipe-item"
        @touchstart.passive="onTouchStart($event, t.id)"
        @touchmove="onTouchMove($event, t.id)"
        @touchend="onTouchEnd(t.id)"
        @mousedown="onTouchStart($event, t.id)"
        @mousemove="onTouchMove($event, t.id)"
        @mouseup="onTouchEnd(t.id)"
        @mouseleave="onTouchEnd(t.id)"
      >
        <!-- 左侧操作按钮（右滑显示） -->
        <div v-if="!showRecycleBin" class="swipe-action left-action" :style="getLeftActionStyle(t.id)">
          <ElIcon :size="24"><component :is="nextStatusIcon[t.status]" /></ElIcon>
          <span class="action-text">{{ nextStatusLabel[t.status] }}</span>
        </div>
        <div v-else class="swipe-action left-action" :style="getLeftActionStyle(t.id)">
          <ElIcon :size="24"><RefreshRight /></ElIcon>
          <span class="action-text">恢复</span>
        </div>
        
        <!-- 右侧操作按钮（左滑显示） -->
        <div v-if="!showRecycleBin" class="swipe-action right-action" :style="getRightActionStyle(t.id)">
          <ElIcon :size="24"><Delete /></ElIcon>
          <span class="action-text">删除</span>
        </div>
        <div v-else class="swipe-action right-action" :style="getRightActionStyle(t.id)">
          <ElIcon :size="24"><Delete /></ElIcon>
          <span class="action-text">永久删除</span>
        </div>

        <!-- 待办卡片 -->
        <ElCard 
          class="todo-card" 
          :class="{ 'is-pinned': t.is_pinned, 'is-deleted': t.is_deleted, 'is-done': t.status === 'done' }"
          :style="getCardStyle(t.id)" 
          @click="handleCardClick(t)"
        >
          <div class="todo-header">
            <div class="todo-title-row">
              <ElIcon v-if="t.is_pinned" class="pin-icon" color="#f56c6c"><Star /></ElIcon>
              <strong :class="{ 'is-done': t.status === 'done' }">{{ t.title }}</strong>
              <!-- 重要性和紧急性标签 -->
              <div class="priority-tags">
                <ElTooltip :content="`重要性: ${t.importance}`" placement="top">
                  <ElTag size="small" :type="getPriorityTagType(t.importance)" effect="light">{{ getPriorityLabel(t.importance) }}</ElTag>
                </ElTooltip>
                <ElTooltip :content="`紧急性: ${t.urgency}`" placement="top">
                  <ElTag size="small" :type="getPriorityTagType(t.urgency)" effect="light">{{ getPriorityLabel(t.urgency) }}</ElTag>
                </ElTooltip>
              </div>
            </div>
          </div>

          <!-- 描述放在标签上面 -->
          <p v-if="t.description" class="todo-description">{{ t.description }}</p>

          <!-- 标签和循环信息放在同一行 -->
          <div class="todo-tags-row">
            <div class="todo-tags">
              <ElTag v-for="tag in parseTags(t.tags)" :key="tag" size="small" effect="plain">{{ tag }}</ElTag>
            </div>
            <div v-if="t.recurrence_type !== 'none'" class="todo-recurrence">
              <ElTag size="small" type="info">
                {{ recurrenceOptions.find(o => o.value === t.recurrence_type)?.label }}
                <span v-if="t.recurrence_type === 'custom'">({{ t.recurrence_interval }}天)</span>
                <span v-if="t.recurrence_count > 0">剩余{{ t.recurrence_count }}次</span>
                <span v-else-if="t.recurrence_count === -1">无限</span>
              </ElTag>
            </div>
          </div>

          <!-- 操作按钮（非回收站模式） -->
          <div v-if="!showRecycleBin" class="todo-actions">
            <div class="todo-actions-left">
              <div class="status-btn-group">
                <ElButton
                  v-for="(s, index) in ['todo', 'in_progress', 'done']"
                  :key="s"
                  size="small"
                  :class="['status-btn', { 'is-first': index === 0, 'is-last': index === 2, 'is-active': t.status === s }]"
                  :type="t.status === s ? 'primary' : ''"
                  :disabled="t.status === s"
                  @click.stop="changeStatus(t, s as TodoStatus)"
                >
                  {{ statusLabel[s] }}
                </ElButton>
              </div>
              <ElButton size="small" :type="t.is_pinned ? 'warning' : ''" @click.stop="handleTogglePin(t)">
                <ElIcon><Star /></ElIcon>
              </ElButton>
            </div>
            <!-- 时间信息显示在最右边 -->
            <div v-if="t.start_date || t.end_date" class="todo-time-inline">
              <span
                v-if="t.end_date"
                class="time-item time-hover-toggle"
                :class="{ 'is-near': isNearDeadline(t.end_date) && !isOverdue(t.end_date), 'is-overdue': isOverdue(t.end_date) }"
              >
                <span class="time-default">截止: {{ formatDateTime(t.end_date) }}</span>
                <span v-if="t.start_date" class="time-hover">开始: {{ formatDateTime(t.start_date) }}</span>
              </span>
              <span v-else-if="t.start_date" class="time-item">开始: {{ formatDateTime(t.start_date) }}</span>
            </div>
          </div>
        </ElCard>
      </div>
      
      <div v-if="currentTodos.length === 0" class="todo-empty">
        <ElEmpty :description="showRecycleBin ? '回收站是空的' : '暂无数据'" />
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <ElDialog
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
    </ElDialog>

    <!-- 新建对话框 -->
    <ElDialog
      v-model="showAdd"
      title="新建待办"
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
            <span style="color: #999; font-size: 14px; padding: 0 4px">至</span>
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
              <span style="color: #666; font-size: 14px">每</span>
              <ElInputNumber v-model="newTodo.recurrence_interval" :min="1" :max="365" style="width: 130px" />
              <span style="color: #666; font-size: 14px">天</span>
            </div>
          </div>
        </ElFormItem>

        <template v-if="newTodo.recurrence_type !== 'none'">
          <ElFormItem label="循环次数">
            <div style="display: flex; align-items: center; gap: 12px">
              <ElInputNumber v-model="newTodo.recurrence_count" :min="-1" :max="999" />
              <span style="color: #999; font-size: 12px">-1=无限，0=不循环</span>
            </div>
          </ElFormItem>
        </template>

        <ElButton type="primary" style="width: 100%" native-type="submit">创建</ElButton>
      </ElForm>
    </ElDialog>

    <!-- 编辑对话框 -->
    <ElDialog
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
            <span style="color: #999; font-size: 14px; padding: 0 4px">至</span>
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
            <span class="existing-tags-label">已有标签：</span>
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
              <span style="color: #666; font-size: 14px">每</span>
              <ElInputNumber v-model="editForm.recurrence_interval" :min="1" :max="365" style="width: 130px" />
              <span style="color: #666; font-size: 14px">天</span>
            </div>
          </div>
        </ElFormItem>

        <template v-if="editForm.recurrence_type !== 'none'">
          <ElFormItem label="循环次数">
            <div style="display: flex; align-items: center; gap: 12px">
              <ElInputNumber v-model="editForm.recurrence_count" :min="-1" :max="999" />
              <span style="color: #999; font-size: 12px">-1=无限，0=不循环</span>
            </div>
          </ElFormItem>
        </template>

        <div style="display: flex; gap: 8px">
          <ElButton type="primary" style="flex: 1" native-type="submit">保存</ElButton>
          <ElButton style="flex: 1" @click="showEdit = false">取消</ElButton>
        </div>
      </ElForm>
    </ElDialog>
  </div>
</template>

<style scoped>
.todos-page {
  display: flex;
  flex-direction: column;
  height: 100%;
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
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.dark .todo-list {
  background: var(--bg-hover);
}

.todo-empty {
  flex: 1;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 滑动容器 */
.todo-swipe-item {
  position: relative;
  touch-action: pan-y;
  user-select: none;
}

/* 滑动操作按钮 */
.swipe-action {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  border-radius: 4px;
  transition: opacity 0.2s ease, transform 0.2s ease;
  pointer-events: none;
}

.left-action {
  left: 0;
  background: linear-gradient(90deg, #18a058 0%, #36ad6a 100%);
}

.right-action {
  right: 0;
  background: linear-gradient(270deg, #f56c6c 0%, #f89898 100%);
}

.action-text {
  margin-top: 4px;
  font-size: 11px;
  white-space: nowrap;
}

.todo-card {
  border-left: 3px solid #18a058;
  border-radius: 12px;
  position: relative;
  z-index: 1;
  background: white;
  cursor: pointer;
  overflow: hidden;
}

.todo-card.is-pinned {
  border-left-color: #f56c6c;
  background: #fff8f8;
}

.todo-card.is-done {
  border-left-color: #909399;
  opacity: 0.85;
  cursor: default;
}

/* 深色模式下保持卡片左边框颜色不变 */
.dark .todo-card {
  border-left-color: #18a058 !important;
}

.dark .todo-card.is-pinned {
  border-left-color: #f56c6c !important;
  background: rgba(245, 108, 108, 0.1);
}

.dark .todo-card.is-done {
  border-left-color: #909399 !important;
  opacity: 0.7;
}

.todo-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.todo-card:not(.is-done):active {
  cursor: grabbing;
}

.dark .todo-card {
  background: var(--el-bg-color);
}

/* 头部 */
.todo-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.todo-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pin-icon {
  color: #f56c6c;
}

.todo-title-row strong {
  font-size: 15px;
  flex: 1;
}

.todo-title-row strong.is-done {
  text-decoration: line-through;
  color: #999;
}

/* 优先级标签 */
.priority-tags {
  display: flex;
  gap: 6px;
  margin-left: auto;
  margin-top: -2px;
}

/* 标签行（标签 + 循环信息） */
.todo-tags-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
}

.todo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.todo-description {
  font-size: 12px;
  color: #666;
  margin: 8px 0;
  line-height: 1.5;
}

.dark .todo-description {
  color: #aaa;
}

/* 四象限徽章（保留供后续使用） */
.quadrant-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin: 4px 0;
}

.quadrant-badge.q-0-0 { background: #f0f0f0; color: #666; }
.quadrant-badge.q-0-1 { background: #e6f7ff; color: #1890ff; }
.quadrant-badge.q-1-0 { background: #f6ffed; color: #52c41a; }
.quadrant-badge.q-1-1 { background: #fff2f0; color: #f5222d; }

.dark .quadrant-badge.q-0-0 { background: #333; color: #999; }
.dark .quadrant-badge.q-0-1 { background: #1a3a4a; color: #4db3ff; }
.dark .quadrant-badge.q-1-0 { background: #1a3a1a; color: #6bd66b; }
.dark .quadrant-badge.q-1-1 { background: #4a1a1a; color: #ff6b6b; }

/* 循环信息 */
.todo-recurrence {
  margin-top: 4px;
}

/* 操作按钮区域 */
.todo-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: nowrap;
}

/* 行内时间显示 */
.todo-time-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}

.todo-time-inline .time-item {
  white-space: nowrap;
}

/* 悬停切换显示开始/截止时间 */
.time-hover-toggle {
  position: relative;
  cursor: pointer;
}

.time-hover-toggle .time-hover {
  display: none;
}

.time-hover-toggle:hover .time-default {
  display: none;
}

.time-hover-toggle:hover .time-hover {
  display: inline;
}

.todo-time-inline .time-item.is-near {
  color: #e6a23c;
  font-weight: 500;
}

.todo-time-inline .time-item.is-overdue {
  color: #f56c6c;
  font-weight: 600;
}

.dark .todo-time-inline {
  color: #aaa;
}

.dark .todo-time-inline .time-item.is-near {
  color: #f5c27a;
}

.dark .todo-time-inline .time-item.is-overdue {
  color: #ff8a8a;
}

/* 操作按钮左侧区域 */
.todo-actions-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 状态按钮组 - 连在一起 */
.status-btn-group {
  display: flex;
}

.status-btn-group .status-btn {
  border-radius: 0;
  margin: 0;
}

.status-btn-group .status-btn.is-first {
  border-top-left-radius: 4px;
  border-bottom-left-radius: 4px;
}

.status-btn-group .status-btn.is-last {
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
}

.status-btn-group .status-btn:not(.is-last) {
  border-right: none;
}

.status-btn-group .status-btn.is-active + .status-btn {
  border-left: none;
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
</style>
