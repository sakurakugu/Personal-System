<script setup lang="ts">
import { Icon } from '@iconify/vue'

const props = defineProps<{
  title: string
  author?: string
  pubDate: string | null | undefined
}>()

function formatDate(date: string | null | undefined) {
  if (!date) return ''
  return new Date(date).toISOString().slice(0, 10)
}
</script>

<template>
  <div class="article-license">
    <div class="license-title">{{ title }}</div>
    <div class="license-grid">
      <div>
        <div class="license-label">作者</div>
        <div class="license-value">{{ author || '匿名' }}</div>
      </div>
      <div>
        <div class="license-label">发布于</div>
        <div class="license-value">{{ formatDate(pubDate) }}</div>
      </div>
      <div>
        <div class="license-label">许可协议</div>
        <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" class="license-link">CC BY-NC-SA 4.0</a>
      </div>
    </div>
    <Icon icon="fa6-brands:creative-commons" class="license-bg-icon" />
  </div>
</template>

<style scoped>
.article-license {
  position: relative;
  overflow: hidden;
  border-radius: 0.75rem;
  background: var(--bg-secondary);
  padding: 1.25rem 1.5rem;
  margin: 1rem 0;
}

.license-title {
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
}

.license-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  position: relative;
  z-index: 1;
}

.license-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-bottom: 0.125rem;
}

.license-value {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  display: -webkit-box;
  overflow: hidden;
}

.license-link {
  font-size: 0.875rem;
  color: var(--el-color-primary);
  font-weight: 500;
  text-decoration: none;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  display: -webkit-box;
  overflow: hidden;
}

.license-link:hover {
  text-decoration: underline;
}

.license-bg-icon {
  position: absolute;
  right: 1.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10rem;
  color: var(--text-primary);
  opacity: 0.04;
  pointer-events: none;
  z-index: 0;
}

.dark .license-bg-icon {
  opacity: 0.06;
}
</style>
