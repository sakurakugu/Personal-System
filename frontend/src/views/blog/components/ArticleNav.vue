<script setup lang="ts">
import { Icon } from '@iconify/vue'

const props = defineProps<{
  prev?: { slug: string; title: string } | null
  next?: { slug: string; title: string } | null
}>()

const emit = defineEmits<{
  navClick: [slug: string]
}>()
</script>

<template>
  <div class="article-nav">
    <div class="nav-item" :class="{ disabled: !prev }" @click="prev && emit('navClick', prev.slug)">
      <Icon icon="material-symbols:chevron-left-rounded" class="nav-icon" />
      <div class="nav-content">
        <div class="nav-label">上一篇</div>
        <div v-if="prev" class="nav-title">{{ prev.title }}</div>
        <div v-else class="nav-title nav-empty">没有更多了</div>
      </div>
    </div>

    <div class="nav-item right" :class="{ disabled: !next }" @click="next && emit('navClick', next.slug)">
      <div class="nav-content">
        <div class="nav-label">下一篇</div>
        <div v-if="next" class="nav-title">{{ next.title }}</div>
        <div v-else class="nav-title nav-empty">没有更多了</div>
      </div>
      <Icon icon="material-symbols:chevron-right-rounded" class="nav-icon" />
    </div>
  </div>
</template>

<style scoped>
.article-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.nav-item:hover:not(.disabled) {
  background: var(--bg-hover);
}

.nav-item:active:not(.disabled) {
  transform: scale(0.98);
}

.nav-item.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.nav-item.right {
  justify-content: flex-end;
  text-align: right;
}

.nav-icon {
  font-size: 1.75rem;
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.nav-content {
  min-width: 0;
  overflow: hidden;
}

.nav-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-bottom: 0.125rem;
}

.nav-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-empty {
  color: var(--text-tertiary);
  font-weight: 400;
}

@media (max-width: 640px) {
  .article-nav {
    grid-template-columns: 1fr;
  }
}
</style>
