<script setup lang="ts">
import { Icon } from '@iconify/vue'

const props = defineProps<{
  publishedAt: string | null | undefined
  updatedAt?: string | null | undefined
  category: { name: string; slug: string } | null | undefined
  tags: { name: string; slug: string }[]
  viewCount?: number
  readingTimeInfo?: { minutes: number; words: number } | null
}>()

const emit = defineEmits<{
  tagClick: [name: string]
}>()

function formatDate(date: string | null | undefined) {
  if (!date) return ''
  return new Date(date).toISOString().slice(0, 10)
}

const publishedStr = formatDate(props.publishedAt)
const updatedStr = formatDate(props.updatedAt)
const hasUpdate = updatedStr && updatedStr !== publishedStr
</script>

<template>
  <div class="article-meta-root">
    <!-- 发布日期 -->
    <div class="meta-item">
      <div class="meta-icon">
        <Icon icon="material-symbols:calendar-today-outline-rounded" class="meta-svg" />
      </div>
      <span class="meta-text">{{ publishedStr }}</span>
    </div>

    <!-- 更新日期 -->
    <div v-if="hasUpdate" class="meta-item">
      <div class="meta-icon">
        <Icon icon="material-symbols:edit-calendar-outline-rounded" class="meta-svg" />
      </div>
      <span class="meta-text">{{ updatedStr }}</span>
    </div>

    <!-- 分类 -->
    <div class="meta-item">
      <div class="meta-icon">
        <Icon icon="material-symbols:book-2-outline-rounded" class="meta-svg" />
      </div>
      <span class="meta-text">{{ category?.name || '未分类' }}</span>
    </div>

    <!-- 标签 -->
    <div v-if="tags.length" class="meta-item">
      <div class="meta-icon">
        <Icon icon="material-symbols:tag-rounded" class="meta-svg" />
      </div>
      <div class="meta-tags">
        <span
          v-for="(tag, i) in tags"
          :key="tag.slug"
          class="meta-tag"
          @click="emit('tagClick', tag.name)"
        >
          {{ tag.name }}
          <span v-if="i < tags.length - 1" class="meta-tag-divider">/</span>
        </span>
      </div>
    </div>

    <!-- 浏览量 -->
    <div v-if="typeof viewCount === 'number'" class="meta-item">
      <div class="meta-icon">
        <Icon icon="material-symbols:visibility-outline-rounded" class="meta-svg" />
      </div>
      <span class="meta-text">{{ viewCount }} 次阅读</span>
    </div>

    <!-- 阅读时间 -->
    <div v-if="readingTimeInfo" class="meta-item">
      <div class="meta-icon">
        <Icon icon="material-symbols:timer-outline-rounded" class="meta-svg" />
      </div>
      <span class="meta-text">约 {{ readingTimeInfo.minutes }} 分钟 · {{ readingTimeInfo.words }} 字</span>
    </div>
  </div>
</template>

<style scoped>
.article-meta-root {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem 1.25rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.meta-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  background: rgba(var(--el-color-primary-rgb), 0.1);
  color: var(--el-color-primary);
  margin-right: 0.5rem;
  transition: all var(--transition-base) ease;
}

.meta-svg {
  font-size: 1.25rem;
}

.meta-text {
  font-weight: 500;
  color: var(--text-secondary);
}

.meta-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.meta-tag {
  cursor: pointer;
  transition: color var(--transition-base) ease;
}

.meta-tag:hover {
  color: var(--el-color-primary);
}

.meta-tag-divider {
  margin: 0 0.375rem;
  color: var(--border-color);
}
</style>
