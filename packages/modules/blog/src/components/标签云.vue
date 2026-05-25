<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { ref } from 'vue'

defineProps<{
  tags: { id: number | string; name: string }[]
}>()

const emit = defineEmits<{
  (e: 'tag-click', name: string): void
}>()

const expanded = ref(false)
</script>

<template>
  <div class="widget-card">
    <div class="widget-header">
      <span>标签</span>
    </div>
    <div class="tag-cloud" :class="{ 'is-collapsed': !expanded && tags.length > 12 }">
      <span
        v-for="tag in tags"
        :key="tag.id"
        class="tag-btn"
        @click="emit('tag-click', tag.name)"
      >
        {{ tag.name }}
      </span>
      <div v-if="tags.length === 0" class="empty-text">暂无标签</div>
    </div>
    <div v-if="tags.length > 12 && !expanded" class="tag-expand" @click="expanded = true">
      <Icon icon="material-symbols:more-horiz" class="tag-expand-icon" />
      <span>更多</span>
    </div>
  </div>
</template>

<style scoped>
.widget-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
}

.widget-card:hover {
  box-shadow: 0 18px 34px rgba(148, 163, 184, 0.18);
}

.dark .widget-card:hover {
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.35);
}

.dark .widget-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
  position: relative;
  margin-left: 32px;
  margin-top: 16px;
  margin-bottom: 8px;
  border-bottom: none;
}

.widget-header::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 5.5px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary);
}

.empty-text {
  width: 100%;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 8px 0;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 16px 16px;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.tag-cloud.is-collapsed {
  max-height: 7.5rem;
  padding-bottom: 0;
}

.tag-expand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px 16px;
  color: var(--primary);
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.tag-expand:hover {
  opacity: 0.8;
}

.tag-expand-icon {
  width: 1.75rem;
  height: 1.75rem;
}

.tag-btn {
  display: inline-flex;
  align-items: center;
  height: 32px;
  font-size: 14px;
  padding: 0 12px;
  border-radius: 8px;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  cursor: pointer;
  transition: all 0.15s;
}

.tag-btn:hover {
  background: var(--btn-regular-bg-hover);
}

.tag-btn:active {
  transform: scale(0.95);
  background: var(--btn-regular-bg-active);
}
</style>
