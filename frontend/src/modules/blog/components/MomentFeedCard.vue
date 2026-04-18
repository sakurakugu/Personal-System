<script setup lang="ts">
import { ElTag, ElText } from 'element-plus'
import type { FeedMomentRecord } from '../../../modules/feed/types'

const props = defineProps<{
  moment: FeedMomentRecord
}>()

function 生成动态摘要(content: string) {
  return content.length > 220 ? `${content.slice(0, 220)}...` : content
}

function 格式化动态时间(date: string | null) {
  if (!date) return '刚刚'
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="feed-card moment-card">
    <div class="moment-header">
      <div class="moment-author">
        <div class="moment-avatar">
          <img v-if="moment.user?.avatar_url" :src="moment.user.avatar_url" :alt="moment.user.nickname || moment.user.username">
          <span v-else>{{ (moment.user?.nickname || moment.user?.username || '我').slice(0, 1) }}</span>
        </div>
        <div class="moment-author-meta">
          <strong>{{ moment.user?.nickname || moment.user?.username || '未知用户' }}</strong>
          <ElText type="info">{{ 格式化动态时间(moment.published_at) }}</ElText>
        </div>
      </div>
      <ElTag size="small" type="success" effect="plain">动态</ElTag>
    </div>
    <h2 v-if="moment.title" class="moment-title">{{ moment.title }}</h2>
    <p class="moment-excerpt">{{ 生成动态摘要(moment.content) }}</p>
  </div>
</template>

<style scoped>
.feed-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.45);
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
  backdrop-filter: blur(18px);
  box-shadow: 0 12px 28px rgba(148, 163, 184, 0.14);
}

.feed-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 36px rgba(148, 163, 184, 0.18);
}

.dark .feed-card:hover {
  box-shadow: 0 18px 36px rgba(2, 6, 23, 0.35);
}

.dark .feed-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

/* Moment Card */
.moment-card {
  padding: 18px 20px;
  background-color: rgba(255, 255, 255, 0.78);
  background-image: linear-gradient(180deg, transparent 0%, oklch(0.96 0.008 var(--hue) / 0.48) 100%);
}

.dark .moment-card {
  background-color: oklch(0.19 0.018 var(--hue) / 0.76);
  background-image: linear-gradient(180deg, transparent 0%, oklch(0.32 0.025 var(--hue) / 0.34) 100%);
}

.moment-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.moment-author {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.moment-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 50%;
  background: var(--theme-accent-gradient);
  color: #fff;
  font-weight: 700;
}

.moment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.moment-author-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.moment-author-meta strong {
  color: var(--text-primary);
  font-size: 14px;
}

.moment-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.moment-excerpt {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 576px) {
  .moment-card {
    padding: 14px;
  }

  .moment-header {
    flex-direction: column;
  }
}
</style>
