<script setup lang="ts">
import { computed } from 'vue'
import { ElTag, ElEmpty } from 'element-plus'
import type { Todo } from '../../../stores/todo'
import TodoList from './TodoList.vue'

const props = defineProps<{
  todos: Todo[]
  showRecycleBin?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', todo: Todo): void
  (e: 'togglePin', todo: Todo): void
  (e: 'delete', id: string, mode: 'soft' | 'permanent'): void
  (e: 'restore', id: string): void
  (e: 'changeStatus', todo: Todo): void
}>()

// 计算四象限分类 (阈值50)
function getQuadrant(todo: Todo): 1 | 2 | 3 | 4 {
  if (todo.importance >= 50 && todo.urgency >= 50) return 1
  if (todo.importance >= 50) return 2
  if (todo.urgency >= 50) return 3
  return 4
}

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
    const q = getQuadrant(todo)
    groups[q].push(todo)
  })
  // 每个象限内：先按状态排序（待办置顶在前，已完成置顶在后），然后按创建时间倒序
  for (const q of [1, 2, 3, 4] as const) {
    groups[q].sort((a, b) => {
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
            @edit="emit('edit', $event)"
            @toggle-pin="emit('togglePin', $event)"
            @delete="(id, mode) => emit('delete', id, mode)"
            @restore="emit('restore', $event)"
            @change-status="emit('changeStatus', $event)"
          />
          <ElEmpty v-else description="暂无待办" :image-size="60" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.todo-quadrants {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.quadrant-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 12px;
  flex: 1;
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
  background-color: rgba(64, 158, 255, 0.1) !important;
}
.dark .quadrant:nth-child(4) {
  background-color: rgba(144, 147, 153, 0.1) !important;
}

/* 响应式：小屏幕时单列显示 */
@media (max-width: 768px) {
  .quadrant-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    overflow-y: auto;
  }
  
  .quadrant {
    min-height: 200px;
  }
}
</style>
