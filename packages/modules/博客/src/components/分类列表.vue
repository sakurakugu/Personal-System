<script setup lang="ts">
import type { CategoryRecord } from '@personal-system/module-articles'

defineProps<{
  categories: CategoryRecord[]
}>()

const emit = defineEmits<{
  (e: 'category-click', slug: string): void
}>()
</script>

<template>
  <div class="widget-card">
    <div class="widget-header">
      <span>分类</span>
    </div>
    <div class="category-list">
      <div
        v-for="cat in categories"
        :key="cat.id"
        class="category-item"
        @click="emit('category-click', cat.slug)"
      >
        <span class="cat-name">{{ cat.name }}</span>
        <span class="cat-count">{{ cat.article_count || 0 }}</span>
      </div>
      <div v-if="categories.length === 0" class="empty-text">暂无分类</div>
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
  box-shadow: 0 12px 28px rgba(148, 163, 184, 0.14);
}

.widget-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(148, 163, 184, 0.18);
}

.dark .widget-card:hover {
  box-shadow: 0 18px 36px rgba(2, 6, 23, 0.35);
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

.category-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 16px 16px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  height: 40px;
  padding-left: 8px;
  padding-right: 8px;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  padding-left: 12px;
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

.category-item:active {
  background: var(--btn-plain-bg-active);
}

.cat-name {
  overflow: hidden;
  text-align: left;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 15px;
}

.cat-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  min-width: 28px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--btn-content);
  background: oklch(0.95 0.025 var(--hue));
  transition: all 0.2s;
}

.dark .cat-count {
  color: var(--deep-text);
  background: var(--primary);
}
</style>
