<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent */
import { reactive } from 'vue'
import { ElCard, ElTag, ElTooltip, ElIcon, ElButton, ElEmpty } from 'element-plus'
import { Star, RefreshRight, Delete, Select } from '@element-plus/icons-vue'
import type { Todo } from '../../../stores/todo'
import { useLongPressSelection } from '../../../composables/useLongPressSelection'
import {
  parseTags,
  getPriorityTagType,
  getPriorityLabel,
  isNearDeadline,
  isOverdue,
  formatDateTime,
  formatPreciseDateTime,
  getTrashExpireAt,
  getTrashRemainingDeleteText,
  recurrenceOptions,
  nextStatusLabel,
  nextStatusIcon,
  useProgressStyle,
} from '../../../composables/useTodoItem'

const props = defineProps<{
  todos: Todo[]
  showRecycleBin?: boolean
  multiSelectMode?: boolean
  selectedIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'edit', todo: Todo): void
  (e: 'togglePin', todo: Todo): void
  (e: 'delete', id: string, mode: 'soft' | 'permanent'): void
  (e: 'restore', id: string): void
  (e: 'changeStatus', todo: Todo): void
  (e: 'longPress', todo: Todo): void
  (e: 'toggleSelect', todo: Todo): void
}>()

const { getProgressStyle } = useProgressStyle()
const { startLongPress, cancelLongPress, consumeLongPress } = useLongPressSelection<Todo>({
  getId: todo => todo.id,
  onLongPress: todo => emit('longPress', todo),
})

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

function initSwipeState(id: string) {
  if (!swipeState[id]) {
    swipeState[id] = { offset: 0, startX: 0, startY: 0, isDragging: false, hasMoved: false }
  }
}

function onTouchStart(e: Event, id: string) {
  if (props.multiSelectMode) return
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
  if (props.multiSelectMode) return
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

  if (Math.abs(deltaX) > 5) {
    state.hasMoved = true
  }

  if (e instanceof TouchEvent && Math.abs(deltaX) > 10) {
    e.preventDefault()
  }

  state.offset = Math.max(-MAX_OFFSET, Math.min(MAX_OFFSET, deltaX))
}

function onTouchEnd(id: string) {
  if (props.multiSelectMode) return
  const state = swipeState[id]
  if (!state) return

  const hadMoved = state.hasMoved
  state.isDragging = false

  if (hadMoved) {
    setTimeout(() => {
      state.hasMoved = false
    }, 50)
  } else {
    state.hasMoved = false
  }

  const todo = props.todos.find(t => t.id === id)
  if (!todo) {
    state.offset = 0
    return
  }

  // 回收站模式：左滑永久删除，右滑恢复
  if (props.showRecycleBin) {
    if (state.offset < -SWIPE_THRESHOLD) {
      emit('delete', id, 'permanent')
      state.offset = 0
      return
    }
    if (state.offset > SWIPE_THRESHOLD) {
      emit('restore', id)
      state.offset = 0
      return
    }
  } else {
    // 正常模式：左滑删除，右滑切换状态
    if (state.offset < -SWIPE_THRESHOLD) {
      emit('delete', id, 'soft')
      state.offset = 0
      return
    }
    if (state.offset > SWIPE_THRESHOLD) {
      emit('changeStatus', todo)
      state.offset = 0
      return
    }
  }

  state.offset = 0
}

function handleCardClick(todo: Todo) {
  if (consumeLongPress(todo)) {
    return
  }
  const state = swipeState[todo.id]
  if (state?.hasMoved) {
    return
  }
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  if (!props.showRecycleBin && todo.status !== 'done') {
    emit('edit', todo)
  }
}

function isSelected(id: string): boolean {
  return props.selectedIds?.includes(id) ?? false
}

function handleTogglePin(todo: Todo) {
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('togglePin', todo)
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
  <div class="todo-list">
    <div
      v-for="t in todos"
      :key="t.id"
      class="todo-swipe-item"
      @touchstart.passive="(event) => { startLongPress(t, event); onTouchStart(event, t.id) }"
      @touchmove="(event) => { cancelLongPress(t); onTouchMove(event, t.id) }"
      @touchend="() => { cancelLongPress(t); onTouchEnd(t.id) }"
      @touchcancel="cancelLongPress(t)"
      @mousedown="(event) => { startLongPress(t, event); onTouchStart(event, t.id) }"
      @mousemove="(event) => { cancelLongPress(t); onTouchMove(event, t.id) }"
      @mouseup="() => { cancelLongPress(t); onTouchEnd(t.id) }"
      @mouseleave="() => { cancelLongPress(t); onTouchEnd(t.id) }"
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
        :class="{ 'is-pinned': t.is_pinned, 'is-deleted': t.is_deleted, 'is-done': t.status === 'done', 'is-selected': isSelected(t.id), 'is-multi-select': multiSelectMode }"
        :style="[getCardStyle(t.id), getProgressStyle(t)]"
        @click="handleCardClick(t)"
      >
        <div v-if="multiSelectMode" class="select-indicator" :class="{ 'is-selected': isSelected(t.id) }">
          <ElIcon><Select /></ElIcon>
        </div>
        <!-- 头部：标题 + 置顶/进度 -->
        <div class="card-header">
          <div class="header-left">
            <div class="title-wrapper">
              <ElIcon v-if="t.is_pinned" class="pin-icon" :size="14"><Star /></ElIcon>
              <span class="title-text" :class="{ 'is-done': t.status === 'done' }">{{ t.title }}</span>
            </div>
          </div>
          <span v-if="t.times_per_interval > 1 && t.recurrence_type !== 'none'" class="interval-progress">
            {{ Math.min(t.interval_progress || 0, t.times_per_interval) }}/{{ t.times_per_interval }}
          </span>
        </div>

        <!-- 描述 -->
        <div v-if="t.description" class="card-description">
          {{ t.description }}
        </div>

        <!-- 底部信息行 -->
        <div class="card-footer">
          <!-- 左边：标签 -->
          <div v-if="parseTags(t.tags).length > 0" class="footer-tags">
            <ElTag v-for="tag in parseTags(t.tags)" :key="tag" size="small" effect="plain">{{ tag }}</ElTag>
          </div>

          <!-- 右边：置顶、重要性、紧急性、循环、时间 -->
          <div class="footer-actions">
            <!-- 回收站保留正常列表的信息展示，但不再提供置顶操作 -->
            <ElButton
              v-if="!showRecycleBin"
              size="small"
              :type="t.is_pinned ? 'warning' : ''"
              @click.stop="handleTogglePin(t)"
            >
              <ElIcon><Star /></ElIcon>
            </ElButton>

            <!-- 重要性 -->
            <ElTooltip :content="`重要性: ${t.importance}`" placement="top">
              <ElTag size="small" :type="getPriorityTagType(t.importance)" effect="light">
                {{ getPriorityLabel(t.importance) }}
              </ElTag>
            </ElTooltip>

            <!-- 紧急性 -->
            <ElTooltip :content="`紧急性: ${t.urgency}`" placement="top">
              <ElTag size="small" :type="getPriorityTagType(t.urgency)" effect="light">
                {{ getPriorityLabel(t.urgency) }}
              </ElTag>
            </ElTooltip>

            <!-- 循环信息 -->
            <ElTag v-if="t.recurrence_type !== 'none'" size="small" type="info">
              <span v-if="t.recurrence_type === 'custom'">每{{ t.recurrence_interval }}天</span>
              <span v-else>{{ recurrenceOptions.find(o => o.value === t.recurrence_type)?.label }}</span>
            </ElTag>

            <!-- 时间信息 -->
            <div v-if="showRecycleBin ? Boolean(t.deleted_at) : Boolean(t.start_date || t.end_date)" class="footer-time">
              <ElTooltip
                v-if="showRecycleBin && t.deleted_at"
                placement="top"
                :show-after="120"
                popper-class="trash-date-tooltip-popper"
              >
                <template #content>
                  <div class="trash-date-tooltip">
                    <div>删除于: {{ formatPreciseDateTime(t.deleted_at) }}</div>
                    <div class="trash-date-tooltip-sub">自动删除于: {{ formatPreciseDateTime(getTrashExpireAt(t.deleted_at)) }}</div>
                  </div>
                </template>
                <span class="time-item time-item-trash">
                  {{ getTrashRemainingDeleteText(t.deleted_at) }}
                </span>
              </ElTooltip>
              <template v-else>
                <span
                  v-if="t.end_date"
                  class="time-item time-hover-toggle"
                  :class="{ 'is-near': !showRecycleBin && isNearDeadline(t.end_date) && !isOverdue(t.end_date), 'is-overdue': !showRecycleBin && isOverdue(t.end_date) }"
                >
                  <span class="time-default">截止: {{ formatDateTime(t.end_date) }}</span>
                  <span v-if="t.start_date" class="time-hover">开始: {{ formatDateTime(t.start_date) }}</span>
                </span>
                <span v-else-if="t.start_date" class="time-item">开始: {{ formatDateTime(t.start_date) }}</span>
              </template>
            </div>
          </div>
        </div>
      </ElCard>
    </div>

    <div v-if="todos.length === 0" class="todo-empty">
      <ElEmpty :description="showRecycleBin ? '回收站是空的' : '暂无数据'" />
    </div>
  </div>
</template>

<style scoped>
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

/* 待办卡片 */
.todo-card {
  border-left: 3px solid #18a058;
  border-radius: 12px;
  position: relative;
  z-index: 1;
  background: white;
  cursor: pointer;
  overflow: hidden;
}

.todo-card.is-selected {
  border-left-color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary-light-9) 78%, white);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 28%, transparent);
}

.todo-card.is-multi-select:not(.is-done) {
  cursor: pointer;
}

.todo-card.is-done {
  border-left-color: #909399;
  background: #f2f3f5;
  --el-card-bg-color: #f2f3f5;
  opacity: 0.85;
  cursor: default;
}

.dark .todo-card {
  border-left-color: #18a058 !important;
  --el-card-bg-color: var(--el-bg-color);
}

.dark .todo-card.is-done {
  border-left-color: #909399 !important;
  background: #2b3138;
  --el-card-bg-color: #2b3138;
  opacity: 0.7;
}

.dark .todo-card.is-selected {
  background: rgba(64, 158, 255, 0.18);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.todo-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.todo-card:not(.is-done):active {
  cursor: grabbing;
}

:deep(.el-card__body) {
  padding: 12px 16px;
}

.select-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  z-index: 2;
}

.select-indicator.is-selected {
  background: var(--el-color-primary);
  color: #fff;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.pin-icon {
  color: #f56c6c;
  flex-shrink: 0;
}

.title-text {
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-text.is-done {
  text-decoration: line-through;
  color: #999;
}

.interval-progress {
  color: #67c23a;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
}

/* 描述 */
.card-description {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-top: 8px;
}

.dark .card-description {
  color: #aaa;
}

/* 底部信息行 */
.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.footer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.footer-actions .el-button {
  height: 20px;
  padding: 0 6px;
}

.footer-time {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.footer-time .time-item {
  white-space: nowrap;
}

.footer-time .time-item-trash {
  cursor: help;
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

.footer-time .time-item.is-near {
  color: #e6a23c;
  font-weight: 500;
}

.footer-time .time-item.is-overdue {
  color: #f56c6c;
  font-weight: 600;
}

.dark .footer-time {
  color: #aaa;
}

.dark .footer-time .time-item.is-near {
  color: #f5c27a;
}

.dark .footer-time .time-item.is-overdue {
  color: #ff8a8a;
}

.trash-date-tooltip {
  display: grid;
  gap: 4px;
  line-height: 1.5;
}

.trash-date-tooltip-sub {
  color: var(--el-text-color-secondary);
}

/* 响应式：小屏幕时底部操作换行 */
@media (max-width: 768px) {
  .card-footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .footer-actions {
    margin-left: 0;
    flex-wrap: wrap;
  }
}
</style>
