<script setup lang="ts">
defineProps<{
  toc: Array<{ id: string; text: string; level: number }>
}>()

const emit = defineEmits<{
  (e: 'item-click', id: string): void
}>()
</script>

<template>
  <div class="widget-card toc-widget">
    <div class="widget-header">
      <span>文章目录</span>
    </div>
    <div class="toc-list">
      <a
        v-for="item in toc"
        :key="item.id"
        :href="`#${item.id}`"
        class="toc-item"
        :class="{ 'toc-h2': item.level === 2, 'toc-h3': item.level === 3 }"
        @click.prevent="emit('item-click', item.id)"
      >
        {{ item.text }}
      </a>
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

.toc-widget .toc-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 16px 16px;
}

.toc-widget .toc-item {
  display: block;
  padding: 6px 10px;
  border-radius: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.toc-widget .toc-item:hover {
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

.toc-widget .toc-h2 {
  font-weight: 500;
}

.toc-widget .toc-h3 {
  padding-left: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
