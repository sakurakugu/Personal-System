<script setup lang="ts">
import type { Todo } from '@personal-system/domain/todos'
import type { WidgetUtilityPanel } from '../types'
import { Refresh } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'
import { ElButton, ElEmpty, ElTag } from 'element-plus'

defineProps<{
  activeUtilityPanel: WidgetUtilityPanel
  formatEndDate: (value: string | null) => string
  isOverdue: (value: string | null) => boolean
  loading: boolean
  orderedTodos: Todo[]
  visible: boolean
}>()

defineEmits<{
  refresh: []
  'toggle-add-panel': []
  'toggle-complete': [id: string]
  'toggle-pin': [id: string]
}>()
</script>

<template>
  <section v-show="visible" class="widget-panel widget-no-drag widget-panel--list">
    <div class="panel-header panel-header--static">
      <div class="panel-header__left">
        <h3 class="panel-header__title">全部待办</h3>
        <ElTag class="widget-count-tag" effect="plain">{{ orderedTodos.length }}</ElTag>
      </div>
      <div class="panel-header__right">
        <ElButton class="widget-icon-button" :icon="Refresh" plain @click="$emit('refresh')" />
        <ElButton
          class="widget-icon-button widget-action-button"
          plain
          title="新建待办"
          :class="{ 'widget-action-button--active': activeUtilityPanel === 'add' }"
          @click="$emit('toggle-add-panel')"
        >
          <Icon icon="mdi:playlist-plus" />
        </ElButton>
      </div>
    </div>

    <div class="panel-body">
      <ElEmpty v-if="!loading && orderedTodos.length === 0" description="暂无待办" />

      <div v-else class="todo-list">
        <article v-for="todo in orderedTodos" :key="todo.id" class="todo-item">
          <button class="todo-check" type="button" :title="todo.status === 'done' ? '标记为未完成' : '标记为完成'" @click="$emit('toggle-complete', todo.id)">
            <Icon :icon="todo.status === 'done' ? 'mdi:checkbox-marked-circle' : 'mdi:checkbox-blank-circle-outline'" />
          </button>

          <div class="todo-item__main">
            <strong>{{ todo.title }}</strong>
            <p :class="{ 'todo-item__meta--warn': isOverdue(todo.end_date) }">
              {{ formatEndDate(todo.end_date) }}
            </p>
          </div>

          <button class="todo-pin" type="button" :title="todo.is_pinned ? '取消置顶' : '置顶'" @click="$emit('toggle-pin', todo.id)">
            <Icon :icon="todo.is_pinned ? 'mdi:star' : 'mdi:star-outline'" />
          </button>
        </article>
      </div>
    </div>
  </section>
</template>

<style>
.widget-action-button--active {
  border-color: color-mix(in srgb, var(--desktop-accent) 34%, var(--desktop-border));
  background: color-mix(in srgb, var(--desktop-accent) 18%, transparent);
}

.widget-count-tag {
  border-radius: 6px;
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: color-mix(in srgb, var(--desktop-accent) 14%, transparent);
  color: var(--desktop-accent);
  cursor: pointer;
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
