<script setup lang="ts">
import { useIntersectionObserver } from '@vueuse/core'
import { Icon } from '@iconify/vue'
import { ElButton, ElMessage, ElTag, ElText } from 'element-plus'
import { ref, watch } from 'vue'
import type { FeedMomentRecord } from '../../../modules/feed/types'
import { likeMoment, recordMomentView } from '../../../modules/moments/api'

const props = defineProps<{
  moment: FeedMomentRecord
}>()

const emit = defineEmits<{
  click: [id: string]
}>()

const cardRef = ref(null)
const likeLoading = ref(false)
const localLikeCount = ref(props.moment.like_count)
const localViewCount = ref(props.moment.view_count)
const hasTrackedView = ref(false)

watch(() => props.moment.like_count, (value) => {
  localLikeCount.value = value
})

watch(() => props.moment.view_count, (value) => {
  localViewCount.value = value
})

function 生成动态摘要(content: string) {
  return content.length > 220 ? `${content.slice(0, 220)}...` : content
}

function 格式化动态时间(date: string | null) {
  if (!date) return '刚刚'
  return new Date(date).toLocaleString('zh-CN')
}

async function handleLike() {
  if (likeLoading.value) return
  likeLoading.value = true
  try {
    const result = await likeMoment(props.moment.id)
    localLikeCount.value = result.like_count
    ElMessage.success(result.changed ? '点赞成功' : '已经点过赞了')
  } catch {
    ElMessage.error('点赞失败')
  } finally {
    likeLoading.value = false
  }
}

async function handleTrackView() {
  try {
    const result = await recordMomentView(props.moment.id)
    localViewCount.value = result.view_count
  } catch {
    // 浏览量记录失败时不影响内容展示。
  }
}

useIntersectionObserver(
  cardRef,
  ([entry]) => {
    if (!entry?.isIntersecting || hasTrackedView.value) {
      return
    }
    hasTrackedView.value = true
    void handleTrackView()
  },
  { threshold: 0.45 },
)

function handleOpenDetail() {
  emit('click', props.moment.id)
}
</script>

<template>
  <div ref="cardRef" class="feed-card moment-card" @click="handleOpenDetail">
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
    <div class="moment-actions">
      <div class="moment-stats">
        <span class="moment-stat">
          <Icon icon="material-symbols:visibility-outline-rounded" />
          <span>{{ localViewCount }}</span>
        </span>
        <span class="moment-stat">
          <Icon icon="material-symbols:favorite-outline-rounded" />
          <span>{{ localLikeCount }}</span>
        </span>
      </div>
      <ElButton class="moment-like-btn" size="small" text :loading="likeLoading" @click.stop="handleLike">
        <Icon icon="material-symbols:favorite-outline-rounded" />
        <span>点赞</span>
      </ElButton>
    </div>
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
  cursor: pointer;
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

.moment-actions {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.moment-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.moment-stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.moment-stat :deep(svg) {
  font-size: 16px;
}

.moment-like-btn {
  color: var(--el-color-primary);
}

@media (max-width: 576px) {
  .moment-card {
    padding: 14px;
  }

  .moment-header {
    flex-direction: column;
  }

  .moment-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
