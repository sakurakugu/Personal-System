<script setup lang="ts">
import { Icon } from '@iconify/vue'

const props = defineProps<{
  title: string
  author?: string
  pubDate: string | null | undefined
  url?: string
}>()

function formatDate(date: string | null | undefined) {
  if (!date) return ''
  return new Date(date).toISOString().slice(0, 10)
}
</script>

<template>
  <div class="article-license">
    <div class="license-title">{{ title }}</div>
    <a v-if="url" :href="url" target="_blank" class="license-url">{{ url }}</a>
    <div class="license-flex">
      <div>
        <div class="license-label">作者</div>
        <div class="license-value">{{ author || 'Sakurakugu' }}</div>
      </div>
      <div>
        <div class="license-label">发布于</div>
        <div class="license-value">{{ formatDate(pubDate) }}</div>
      </div>
      <div>
        <div class="license-label">许可协议</div>
        <a
          href="https://creativecommons.org/licenses/by-nc-sa/4.0/"
          target="_blank"
          class="license-link"
        >CC BY-NC-SA 4.0</a>
      </div>
    </div>
    <Icon icon="fa6-brands:creative-commons" class="license-bg-icon" />
  </div>
</template>

<style scoped>
.article-license {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  padding: 1.25rem 1.5rem;
  margin: 0;
}

.dark .article-license {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.license-title {
  font-weight: 700;
  color: rgba(0, 0, 0, 0.75);
  margin-bottom: 0.25rem;
  position: relative;
  z-index: 1;
}

.dark .license-title {
  color: rgba(255, 255, 255, 0.75);
}

.license-url {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--el-color-primary);
  text-decoration: none;
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.license-url:hover {
  text-decoration: underline;
}

.license-flex {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  position: relative;
  z-index: 1;
}

.license-label {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.3);
  margin-bottom: 0.125rem;
}

.dark .license-label {
  color: rgba(255, 255, 255, 0.3);
}

.license-value {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.75);
  font-weight: 500;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  display: -webkit-box;
  overflow: hidden;
}

.dark .license-value {
  color: rgba(255, 255, 255, 0.75);
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
  font-size: 15rem;
  color: rgba(0, 0, 0, 0.05);
  opacity: 1;
  pointer-events: none;
  z-index: 0;
}

.dark .license-bg-icon {
  color: rgba(255, 255, 255, 0.05);
}
</style>
