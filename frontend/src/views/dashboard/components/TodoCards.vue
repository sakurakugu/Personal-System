<script setup lang="ts">
/* global MouseEvent */
import { ElCard, ElCheckbox, ElTag, ElTooltip, ElIcon } from 'element-plus'
import { Star, Calendar, Select } from '@element-plus/icons-vue'
import type { Todo } from '../../../stores/todo'
import { useLongPressSelection } from '../../../composables/useLongPressSelection'
import {
  parseTags,
  getPriorityTagType,
  getPriorityLabel,
  isNearDeadline,
  isOverdue,
  formatDateTime,
  getRecurrenceText,
  useSortedByQuadrant,
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

// 按象限排序的待办
const sortedTodos = useSortedByQuadrant(props.todos)

function handleCardClick(todo: Todo) {
  if (consumeLongPress(todo)) return
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  if (props.showRecycleBin || todo.status === 'done') return
  emit('edit', todo)
}

function isSelected(id: string): boolean {
  return props.selectedIds?.includes(id) ?? false
}

function handleCheckboxChange(todo: Todo) {
  if (props.multiSelectMode) {
    emit('toggleSelect', todo)
    return
  }
  emit('changeStatus', todo)
}
</script>

<template>
  <div class="todo-cards">
    <div class="cards-grid">
      <ElCard
        v-for="t in sortedTodos"
        :key="t.id"
        class="todo-card"
        :class="{ 'is-pinned': t.is_pinned, 'is-done': t.status === 'done', 'is-selected': isSelected(t.id), 'is-multi-select': multiSelectMode }"
        :style="getProgressStyle(t)"
        @touchstart.passive="startLongPress(t, $event)"
        @touchmove="cancelLongPress(t)"
        @touchend="cancelLongPress(t)"
        @touchcancel="cancelLongPress(t)"
        @mousedown="startLongPress(t, $event)"
        @mousemove="cancelLongPress(t)"
        @mouseup="cancelLongPress(t)"
        @mouseleave="cancelLongPress(t)"
        @click="handleCardClick(t)"
      >
        <div v-if="multiSelectMode" class="select-indicator" :class="{ 'is-selected': isSelected(t.id) }">
          <ElIcon><Select /></ElIcon>
        </div>
        <!-- 头部：复选框 + 标题 + 置顶/进度 -->
        <div class="card-header">
          <div class="header-left">
            <ElCheckbox
              :model-value="t.status === 'done'"
              @click.stop
              @mousedown.stop
              @touchstart.stop
              @change="handleCheckboxChange(t)"
            />
            <div class="title-wrapper">
              <ElIcon v-if="t.is_pinned" class="pin-icon" :size="14"><Star /></ElIcon>
              <span class="title-text" :class="{ 'is-done': t.status === 'done' }">{{ t.title }}</span>
            </div>
          </div>
          <div class="header-right">
            <span v-if="t.times_per_interval > 1 && t.recurrence_type !== 'none'" class="interval-progress">
              {{ Math.min(t.interval_progress || 0, t.times_per_interval) }}/{{ t.times_per_interval }}
            </span>
          </div>
        </div>

        <!-- 描述 -->
        <div v-if="t.description" class="card-description">
          {{ t.description.length > 100 ? t.description.substring(0, 100) + '...' : t.description }}
        </div>

        <!-- 标签 -->
        <div v-if="parseTags(t.tags).length > 0" class="card-tags">
          <ElTag v-for="tag in parseTags(t.tags)" :key="tag" size="small" effect="plain">{{ tag }}</ElTag>
        </div>

        <!-- 底部信息 -->
        <div class="card-footer">
          <div class="footer-priority">
            <ElTooltip :content="`重要性: ${t.importance}`" placement="top">
              <ElTag size="small" :type="getPriorityTagType(t.importance)" effect="light">
                {{ getPriorityLabel(t.importance) }}
              </ElTag>
            </ElTooltip>
            <ElTooltip :content="`紧急性: ${t.urgency}`" placement="top">
              <ElTag size="small" :type="getPriorityTagType(t.urgency)" effect="light">
                {{ getPriorityLabel(t.urgency) }}
              </ElTag>
            </ElTooltip>
          </div>
          <div class="footer-meta">
            <ElTag v-if="t.recurrence_type !== 'none'" size="small" type="info">
              {{ getRecurrenceText(t.recurrence_type, t.recurrence_interval) }}
            </ElTag>
            <!-- 时间显示：悬停切换显示开始/截止时间 -->
            <span
              v-if="t.end_date || t.start_date"
              class="time-item"
              :class="[
                (t.end_date && isNearDeadline(t.end_date) && !isOverdue(t.end_date)) ? 'is-near' : '',
                (t.end_date && isOverdue(t.end_date)) ? 'is-overdue' : '',
                t.start_date && t.end_date ? 'time-hover-toggle' : ''
              ]"
            >
              <ElIcon :size="12"><Calendar /></ElIcon>
              <template v-if="t.start_date && t.end_date">
                <span class="time-default">{{ formatDateTime(t.end_date) }}</span>
                <span class="time-hover">{{ formatDateTime(t.start_date) }}</span>
              </template>
              <span v-else-if="t.end_date">{{ formatDateTime(t.end_date) }}</span>
              <span v-else-if="t.start_date">{{ formatDateTime(t.start_date) }}</span>
            </span>
          </div>
        </div>
      </ElCard>
    </div>
  </div>
</template>

<style scoped>
.todo-cards {
  padding: 4px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

:deep(.el-card) {
  width: 100%;
}

.todo-card {
  border-radius: 12px;
  border-left: 3px solid #18a058;
  cursor: pointer;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  position: relative;
}

.todo-card.is-selected {
  border-left-color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary-light-9) 80%, white);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 28%, transparent);
}

.todo-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.todo-card.is-done {
  border-left-color: #909399;
  opacity: 0.85;
  cursor: default;
}

.todo-card.is-done:hover {
  transform: none;
}

.dark .todo-card {
  border-left-color: #18a058;
}

.dark .todo-card.is-done {
  border-left-color: #909399;
  opacity: 0.7;
}

.dark .todo-card.is-selected {
  background: rgba(64, 158, 255, 0.18);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

:deep(.el-card__body) {
  padding: 12px;
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

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
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

.header-right {
  flex-shrink: 0;
}

.interval-progress {
  color: #67c23a;
  font-weight: 600;
  font-size: 13px;
}

.card-description {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.dark .card-description {
  color: #aaa;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.card-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
}

.footer-priority {
  display: flex;
  gap: 4px;
}

.footer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
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

.time-item.is-near {
  color: #e6a23c;
  font-weight: 500;
}

.time-item.is-overdue {
  color: #f56c6c;
  font-weight: 600;
}

.dark .footer-meta {
  color: #aaa;
}

.dark .time-item.is-near {
  color: #f5c27a;
}

.dark .time-item.is-overdue {
  color: #ff8a8a;
}
</style>
