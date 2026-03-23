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
  ElTag,
} from 'element-plus'
import { List, RefreshRight, CircleCheckFilled, Delete, Check, Clock, WarningFilled } from '@element-plus/icons-vue'
import { useTodoStore, type Todo } from '../../stores/todo'

const todoStore = useTodoStore()

const showAdd = ref(false)
const newTodo = ref({ title: '', description: '', priority: 2, due_date: null as Date | null })

// 编辑相关
const showEdit = ref(false)
const editingTodo = ref<Todo | null>(null)
const editForm = ref({ title: '', description: '', priority: 2, due_date: null as Date | null, status: 'todo' })
// 选中的状态（多选）
const selectedStatuses = ref<string[]>(['todo', 'in_progress'])

// 切换状态选择（多选框点击）
function toggleStatus(status: string) {
  const index = selectedStatuses.value.indexOf(status)
  if (index > -1) {
    // 至少保留一个选中
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

// 判断是否选中
function isStatusSelected(status: string): boolean {
  return selectedStatuses.value.includes(status)
}

// 删除确认相关
const showDeleteConfirm = ref(false)
const todoToDelete = ref<string | null>(null)
const dontAskAgain = ref(false)
const DELETE_CONFIRM_KEY = 'todo_delete_confirm_dont_ask'

// 检查 sessionStorage 中是否设置了不再询问
function shouldSkipConfirm(): boolean {
  try {
    return sessionStorage.getItem(DELETE_CONFIRM_KEY) === 'true'
  } catch {
    return false
  }
}

// 设置不再询问
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
}>>({})

const SWIPE_THRESHOLD = 80 // 滑动触发阈值
const MAX_OFFSET = 120 // 最大偏移量

onMounted(() => todoStore.fetchTodos())

const statusGroups = computed(() => ({
  all: todoStore.todos,
  todo: todoStore.todos.filter(t => t.status === 'todo'),
  in_progress: todoStore.todos.filter(t => t.status === 'in_progress'),
  done: todoStore.todos.filter(t => t.status === 'done'),
}))

// 当前显示的待办（多选过滤）
const currentTodos = computed(() => {
  if (selectedStatuses.value.includes('all')) {
    return todoStore.todos
  }
  return todoStore.todos.filter(t => selectedStatuses.value.includes(t.status))
})

const priorityOptions = [
  { label: '高', value: 1 },
  { label: '中', value: 2 },
  { label: '低', value: 3 },
]

const priorityLabel: Record<number, string> = { 1: '高', 2: '中', 3: '低' }

const statusLabel: Record<string, string> = {
  all: '全部',
  todo: '待办',
  in_progress: '进行中',
  done: '已完成',
}
const statusIcon = {
  all: List,
  todo: List,
  in_progress: RefreshRight,
  done: CircleCheckFilled,
}

const priorityTag: Record<number, 'danger' | 'warning' | 'success'> = { 1: 'danger', 2: 'warning', 3: 'success' }

// 状态切换顺序: todo -> in_progress -> done -> todo
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

async function addTodo() {
  if (!newTodo.value.title.trim()) return
  try {
    await todoStore.addTodo({
      title: newTodo.value.title,
      description: newTodo.value.description || undefined,
      priority: newTodo.value.priority,
      due_date: newTodo.value.due_date ? newTodo.value.due_date.toISOString() : undefined,
    })
    showAdd.value = false
    newTodo.value = { title: '', description: '', priority: 2, due_date: null }
    ElMessage.success('创建成功')
  } catch { ElMessage.error('创建失败') }
}

// 打开编辑对话框
function openEdit(todo: Todo) {
  editingTodo.value = todo
  editForm.value = {
    title: todo.title,
    description: todo.description || '',
    priority: todo.priority,
    due_date: todo.due_date ? new Date(todo.due_date) : null,
    status: todo.status,
  }
  showEdit.value = true
}

// 保存编辑
async function saveEdit() {
  if (!editingTodo.value || !editForm.value.title.trim()) return
  try {
    await todoStore.updateTodo(editingTodo.value.id, {
      title: editForm.value.title,
      description: editForm.value.description || undefined,
      priority: editForm.value.priority,
      due_date: editForm.value.due_date ? editForm.value.due_date.toISOString() : undefined,
      status: editForm.value.status,
    })
    showEdit.value = false
    editingTodo.value = null
    ElMessage.success('保存成功')
  } catch { ElMessage.error('保存失败') }
}

async function changeStatus(todo: Todo, status: string) {
  await todoStore.updateTodo(todo.id, { status })
}

async function removeTodo(id: string) {
  await todoStore.deleteTodo(id)
  ElMessage.success('已删除')
}

// 处理删除请求（带确认逻辑）
function handleDeleteRequest(id: string) {
  if (shouldSkipConfirm()) {
    // 直接删除
    removeTodo(id)
  } else {
    // 显示确认对话框
    todoToDelete.value = id
    dontAskAgain.value = false
    showDeleteConfirm.value = true
  }
}

// 确认删除
function confirmDelete() {
  if (todoToDelete.value) {
    setDontAskAgain(dontAskAgain.value)
    removeTodo(todoToDelete.value)
    todoToDelete.value = null
  }
  showDeleteConfirm.value = false
}

// 取消删除
function cancelDelete() {
  todoToDelete.value = null
  showDeleteConfirm.value = false
}

// 触摸/鼠标事件处理
function initSwipeState(id: string) {
  if (!swipeState[id]) {
    swipeState[id] = { offset: 0, startX: 0, startY: 0, isDragging: false }
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

  // 如果垂直滑动更大，忽略本次滑动
  if (Math.abs(deltaY) > Math.abs(deltaX)) return

  // 阻止默认行为（防止页面滚动）
  if (e instanceof TouchEvent && Math.abs(deltaX) > 10) {
    e.preventDefault()
  }

  // 限制偏移量
  state.offset = Math.max(-MAX_OFFSET, Math.min(MAX_OFFSET, deltaX))
}

function onTouchEnd(id: string) {
  const state = swipeState[id]
  if (!state) return

  state.isDragging = false

  const todo = todoStore.todos.find(t => t.id === id)
  if (!todo) {
    state.offset = 0
    return
  }

  // 向左滑动超过阈值：删除
  if (state.offset < -SWIPE_THRESHOLD) {
    handleDeleteRequest(id)
    state.offset = 0
    return
  }

  // 向右滑动超过阈值：切换状态
  if (state.offset > SWIPE_THRESHOLD) {
    const nextStatus = statusOrder[todo.status]
    changeStatus(todo, nextStatus)
    ElMessage.success(`${todo.title} 已${nextStatusLabel[todo.status]}`)
    state.offset = 0
    return
  }

  // 未超过阈值，恢复原位
  state.offset = 0
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
</script>

<template>
  <div class="todos-page">
    <div class="todos-header">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><List /></ElIcon>
        <span>待办事项</span>
      </h2>
      <ElButton type="primary" @click="showAdd = true">+ 新建</ElButton>
    </div>

    <div class="status-bar">
      <ElPopover trigger="click" :width="180" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
        <template #reference>
          <ElButton>
            <span style="display: flex; align-items: center; gap: 6px">
              <ElIcon><List /></ElIcon>
              <span>
                {{ selectedStatuses.length === 1 ? statusLabel[selectedStatuses[0]] : `已选${selectedStatuses.length}项` }}
                ({{ currentTodos.length }})
              </span>
              <span style="margin-left: 4px">▼</span>
            </span>
          </ElButton>
        </template>
        <div class="status-filter-list">
          <div
            v-for="key in ['todo', 'in_progress', 'done', 'all']"
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
        <div class="swipe-action left-action" :style="getLeftActionStyle(t.id)">
          <ElIcon :size="24"><component :is="nextStatusIcon[t.status]" /></ElIcon>
          <span class="action-text">{{ nextStatusLabel[t.status] }}</span>
        </div>
        
        <!-- 右侧操作按钮（左滑显示） -->
        <div class="swipe-action right-action" :style="getRightActionStyle(t.id)">
          <ElIcon :size="24"><Delete /></ElIcon>
          <span class="action-text">删除</span>
        </div>

        <!-- 待办卡片 -->
        <ElCard class="todo-card" :style="getCardStyle(t.id)" @click="openEdit(t)">
          <div style="display: flex; justify-content: space-between; align-items: start">
            <strong>{{ t.title }}</strong>
            <ElTag :type="priorityTag[t.priority]" size="small">{{ priorityLabel[t.priority] }}</ElTag>
          </div>
          <p v-if="t.description" style="font-size: 12px; color: #888; margin: 4px 0">{{ t.description }}</p>
          <p v-if="t.due_date" style="font-size: 11px; color: #aaa">截止: {{ new Date(t.due_date).toLocaleDateString() }}</p>
          <div class="todo-actions">
            <div class="status-btn-group">
              <ElButton
                v-for="(status, index) in ['todo', 'in_progress', 'done']"
                :key="status"
                size="small"
                :class="['status-btn', { 'is-first': index === 0, 'is-last': index === 2, 'is-active': t.status === status }]"
                :type="t.status === status ? 'primary' : ''"
                :disabled="t.status === status"
                @click.stop="changeStatus(t, status)"
              >
                {{ statusLabel[status] }}
              </ElButton>
            </div>
          </div>
        </ElCard>
      </div>
      <div v-if="currentTodos.length === 0" class="todo-empty">
        <ElEmpty description="暂无数据" />
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
        <span>确定要删除这个待办事项吗？</span>
      </div>
      <div style="margin-top: 16px; padding-left: 52px">
        <ElCheckbox v-model="dontAskAgain">本次都不再询问（刷新后恢复）</ElCheckbox>
      </div>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <ElButton @click="cancelDelete">取消</ElButton>
          <ElButton type="danger" @click="confirmDelete">删除</ElButton>
        </div>
      </template>
    </ElDialog>

    <ElDialog
      :model-value="showAdd"
      title="新建待办"
      width="480px"
      style="max-width: 90vw"
      @update:model-value="showAdd = $event"
    >
      <ElForm label-position="left" label-width="70px" @submit.prevent="addTodo">
        <ElFormItem label="标题">
          <ElInput v-model="newTodo.title" placeholder="待办标题" />
        </ElFormItem>
        <ElFormItem label="描述">
          <ElInput v-model="newTodo.description" type="textarea" placeholder="可选描述" />
        </ElFormItem>
        <ElFormItem label="优先级">
          <ElSelect v-model="newTodo.priority">
            <ElOption v-for="item in priorityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="截止日期">
          <ElDatePicker v-model="newTodo.due_date" type="date" clearable style="width: 100%" />
        </ElFormItem>
        <ElButton type="primary" style="width: 100%" native-type="submit">创建</ElButton>
      </ElForm>
    </ElDialog>

    <!-- 编辑对话框 -->
    <ElDialog
      :model-value="showEdit"
      title="编辑待办"
      width="480px"
      style="max-width: 90vw"
      @update:model-value="showEdit = $event"
    >
      <ElForm label-position="left" label-width="70px" @submit.prevent="saveEdit">
        <ElFormItem label="标题">
          <ElInput v-model="editForm.title" placeholder="待办标题" />
        </ElFormItem>
        <ElFormItem label="描述">
          <ElInput v-model="editForm.description" type="textarea" placeholder="可选描述" />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="editForm.status">
            <ElOption v-for="key in ['todo', 'in_progress', 'done']" :key="key" :label="statusLabel[key]" :value="key" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="优先级">
          <ElSelect v-model="editForm.priority">
            <ElOption v-for="item in priorityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="截止日期">
          <ElDatePicker v-model="editForm.due_date" type="date" clearable style="width: 100%" />
        </ElFormItem>
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
  position: relative;
  z-index: 1;
  background: white;
  cursor: pointer;
}

.todo-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.todo-card:active {
  cursor: grabbing;
}

.dark .todo-card {
  background: var(--el-bg-color);
}

/* 操作按钮区域 */
.todo-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
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

/* 相邻按钮的边框处理 */
.status-btn-group .status-btn:not(.is-last) {
  border-right: none;
}

.status-btn-group .status-btn.is-active + .status-btn {
  border-left: none;
}

/* 确保禁用状态的样式正确 */
.status-btn-group .el-button.is-disabled {
  background-color: var(--el-button-bg-color);
  border-color: var(--el-button-border-color);
}

/* 滑动提示覆盖层 */
.todo-card::before,
.todo-card::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.todo-card.dragging-left::after {
  right: 0;
  background: #f56c6c;
  opacity: 1;
}

.todo-card.dragging-right::before {
  left: 0;
  background: #18a058;
  opacity: 1;
}

/* 状态筛选器样式 */
.status-filter-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
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
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}
</style>
