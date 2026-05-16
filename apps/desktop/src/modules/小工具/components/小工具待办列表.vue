<script setup lang="ts">
import type { Todo } from '@personal-system/domain/todos'
import type { WidgetUtilityPanel } from '../types'
import { Refresh } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { ElEmpty, ElTag } from 'element-plus'
import { computed } from 'vue'
import WidgetButton from './小工具按钮.vue'

const props = defineProps<{
  activeUtilityPanel: WidgetUtilityPanel
  formatEndDate: (value: string | null) => string
  isOverdue: (value: string | null) => boolean
  loadedOnce: boolean
  loading: boolean
  orderedTodos: Todo[]
}>()

defineEmits<{
  refresh: []
  'toggle-add-panel': []
  'toggle-complete': [id: string]
  'toggle-pin': [id: string]
}>()

const shouldShowEmpty = computed(() => props.loadedOnce && props.orderedTodos.length === 0)
</script>

<template>
  <section class="widget-panel widget-no-drag widget-panel--list">
    <div class="panel-header panel-header--static">
      <div class="panel-header__left">
        <h3 class="panel-header__title">全部待办</h3>
        <ElTag class="widget-count-tag" effect="plain">{{ orderedTodos.length }}</ElTag>
      </div>
      <div class="panel-header__right">
        <WidgetButton title="刷新待办" :loading="loading" @click="$emit('refresh')">
          <template #icon>
            <Refresh />
          </template>
        </WidgetButton>
        <WidgetButton
          title="新建待办"
          :active="activeUtilityPanel === 'add'"
          @click="$emit('toggle-add-panel')"
        >
          <template #icon>
            <Icon icon="mdi:playlist-plus" />
          </template>
        </WidgetButton>
      </div>
    </div>

    <div class="panel-body">
      <ElEmpty v-if="shouldShowEmpty" class="todo-empty" description="暂无待办" />

      <div v-else class="todo-list">
        <article v-for="todo in orderedTodos" :key="todo.id" class="todo-item">
          <WidgetButton
            class="todo-check"
            size="compact"
            :active="todo.status === 'done'"
            :title="todo.status === 'done' ? '标记为未完成' : '标记为完成'"
            @click="$emit('toggle-complete', todo.id)"
          >
            <template #icon>
              <Icon :icon="todo.status === 'done' ? 'mdi:checkbox-marked-circle' : 'mdi:checkbox-blank-circle-outline'" />
            </template>
          </WidgetButton>

          <div class="todo-item__main">
            <strong>{{ todo.title }}</strong>
            <p :class="{ 'todo-item__meta--warn': isOverdue(todo.end_date) }">
              {{ formatEndDate(todo.end_date) }}
            </p>
          </div>

          <WidgetButton
            class="todo-pin"
            size="compact"
            :active="todo.is_pinned"
            :title="todo.is_pinned ? '取消置顶' : '置顶'"
            @click="$emit('toggle-pin', todo.id)"
          >
            <template #icon>
              <Icon :icon="todo.is_pinned ? 'mdi:star' : 'mdi:star-outline'" />
            </template>
          </WidgetButton>
        </article>
      </div>
    </div>
  </section>
</template>

<style>
.widget-count-tag {
  border-radius: 6px;
}

.todo-empty {
  min-height: 160px;
}

.todo-list {
  display: grid;
  gap: 10px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--widget-window-radius);
  background: color-mix(in srgb, var(--desktop-accent) 20%, transparent);
}

.todo-check,
.todo-pin {
  border: none;
}

.todo-item__main {
  min-width: 0;
  flex: 1;
}

.todo-item__main strong,
.todo-item__main p {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-item__main strong {
  color: var(--desktop-text);
}

.todo-item__meta--warn {
  color: var(--el-color-danger);
}
</style>
