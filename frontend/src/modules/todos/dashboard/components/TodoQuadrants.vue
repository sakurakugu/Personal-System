<script setup lang="ts">
import { computed } from 'vue'
import { ElTag, ElEmpty } from 'element-plus'
import type { Todo } from '../../store'
import { getQuadrant, sortTodosByStatusAndPinCreated } from '../../helpers/todo-item'
import TodoList from './TodoList.vue'

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

// 象限配置
const quadrantsConfig = {
  1: { title: '重要且紧急', color: '#f56c6c', bgColor: '#fef0f0', tagType: 'danger' as const },
  2: { title: '重要不紧急', color: '#e6a23c', bgColor: '#fdf6ec', tagType: 'warning' as const },
  3: { title: '不重要紧急', color: '#409eff', bgColor: '#ecf5ff', tagType: 'info' as const },
  4: { title: '不重要不紧急', color: '#909399', bgColor: '#f4f4f5', tagType: 'info' as const },
}

// 按象限分组的待办
const groupedTodos = computed(() => {
  const groups: Record<number, Todo[]> = { 1: [], 2: [], 3: [], 4: [] }
  props.todos.forEach(todo => {
    const q = getQuadrant(todo.importance, todo.urgency)
    groups[q].push(todo)
  })
  for (const q of [1, 2, 3, 4] as const) {
    groups[q] = sortTodosByStatusAndPinCreated(groups[q])
  }
  return groups
})
</script>

<template>
  <div class="todo-quadrants">
    <div class="quadrant-grid">
      <!-- 四个象限 -->
      <div
        v-for="q in [1, 2, 3, 4] as const"
        :key="q"
        class="quadrant"
        :style="{ backgroundColor: quadrantsConfig[q].bgColor }"
      >
        <!-- 象限标题 -->
        <div class="quadrant-header">
          <span class="quadrant-title" :style="{ color: quadrantsConfig[q].color }">
            {{ quadrantsConfig[q].title }}
          </span>
          <ElTag :type="quadrantsConfig[q].tagType" size="small">
            {{ groupedTodos[q].length }}
          </ElTag>
        </div>

        <!-- 象限内容 - 使用 TodoList -->
        <div class="quadrant-body">
          <TodoList
            v-if="groupedTodos[q].length > 0"
            :todos="groupedTodos[q]"
            :show-recycle-bin="showRecycleBin"
            :multi-select-mode="multiSelectMode"
            :selected-ids="selectedIds"
            @edit="emit('edit', $event)"
            @toggle-pin="emit('togglePin', $event)"
            @delete="(id, mode) => emit('delete', id, mode)"
            @restore="emit('restore', $event)"
            @change-status="emit('changeStatus', $event)"
            @long-press="emit('longPress', $event)"
            @toggle-select="emit('toggleSelect', $event)"
          />
          <ElEmpty v-else description="暂无待办" :image-size="60" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../../../../styles/media.css';

.todo-quadrants {
  flex: 1;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.quadrant-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: 12px;
  flex: 1;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.quadrant {
  border-radius: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.dark .quadrant {
  border-color: var(--el-border-color);
}

.quadrant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.quadrant-title {
  font-weight: 600;
  font-size: 15px;
}

.quadrant-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

/* 深色模式象限背景色 */
.dark .quadrant:nth-child(1) {
  background-color: rgba(245, 108, 108, 0.1) !important;
}
.dark .quadrant:nth-child(2) {
  background-color: rgba(230, 162, 60, 0.1) !important;
}
.dark .quadrant:nth-child(3) {
  background-color: rgb(var(--el-color-primary-rgb) / 0.1) !important;
}
.dark .quadrant:nth-child(4) {
  background-color: rgba(144, 147, 153, 0.1) !important;
}

/* 响应式：小屏幕时单列显示 */
@media (--mobile-viewport) {
  .quadrant-grid {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, minmax(0, 1fr));
    overflow: hidden;
  }
  
  .quadrant {
    min-height: 0;
  }
}
</style>
