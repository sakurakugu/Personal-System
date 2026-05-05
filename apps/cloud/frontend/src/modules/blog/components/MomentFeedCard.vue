<script setup lang="ts">
import { useIntersectionObserver } from '@vueuse/core'
import { Icon } from '@iconify/vue'
import { ElButton, ElMessage, ElText } from 'element-plus'
import { ref, watch } from 'vue'
import type { FeedMomentRecord } from '../../../modules/feed/types'
import { likeMoment, recordMomentView, unlikeMoment } from '../../../modules/moments/api'
import { resolveManagedFileUrl } from '../../../shared/utils/managedFile'

const props = defineProps<{
  moment: FeedMomentRecord
}>()

const emit = defineEmits<{
  click: [id: string]
}>()

const cardRef = ref(null)
const likeLoading = ref(false)
const localLikeCount = ref(props.moment.like_count)
const localLiked = ref(props.moment.liked)
const localViewCount = ref(props.moment.view_count)
const hasTrackedView = ref(false)

watch(() => props.moment.like_count, (value) => {
  localLikeCount.value = value
})

watch(() => props.moment.liked, (value) => {
  localLiked.value = value
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

function 获取编辑提示(publishedAt: string | null, lastEditedAt: string) {
  if (!publishedAt) return ''
  if (new Date(lastEditedAt).getTime() <= new Date(publishedAt).getTime()) {
    return ''
  }
  return `编辑于 ${格式化动态时间(lastEditedAt)}`
}

function 获取动态图片预览地址(url: string) {
  return resolveManagedFileUrl(url)
}

async function handleLike() {
  if (likeLoading.value) return
  likeLoading.value = true
  try {
    const result = localLiked.value
      ? await unlikeMoment(props.moment.id)
      : await likeMoment(props.moment.id)
    localLikeCount.value = result.like_count
    localLiked.value = result.liked
    if (result.changed) {
      ElMessage.success(result.liked ? '点赞成功' : '已取消点赞')
    } else {
      ElMessage.info(result.liked ? '已经点过赞了' : '当前还没有点赞')
    }
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
          <img
            v-if="moment.user?.avatar_url"
            :src="moment.user.avatar_url"
            :alt="moment.user.nickname || moment.user.username"
            loading="lazy"
            decoding="async"
          >
          <span v-else>{{ (moment.user?.nickname || moment.user?.username || '我').slice(0, 1) }}</span>
        </div>
        <div class="moment-author-meta">
          <strong>{{ moment.user?.nickname || moment.user?.username || '未知用户' }}</strong>
          <ElText type="info" :title="获取编辑提示(moment.published_at, moment.last_edited_at) || undefined">
            {{ 格式化动态时间(moment.published_at) }}
          </ElText>
        </div>
      </div>
      <div class="moment-like-group">
        <ElButton
          class="moment-like-btn"
          size="small"
          text
          :loading="likeLoading"
          :aria-label="localLiked ? '取消点赞' : '点赞'"
          :title="localLiked ? '取消点赞' : '点赞'"
          @click.stop="handleLike"
        >
          <Icon :icon="localLiked ? 'material-symbols:favorite-rounded' : 'material-symbols:favorite-outline-rounded'" />
        </ElButton>
        <span class="moment-like-count">{{ localLikeCount }}</span>
      </div>
    </div>
    <h2 v-if="moment.title" class="moment-title">{{ moment.title }}</h2>
    <p class="moment-excerpt">{{ 生成动态摘要(moment.content) }}</p>
    <div v-if="moment.images.length > 0" class="moment-image-strip">
      <img
        v-for="image in moment.images.slice(0, 3)"
        :key="image.id"
        :src="获取动态图片预览地址(image.thumbnail_url || image.preview_url || image.url)"
        :alt="image.original_name"
        loading="lazy"
        decoding="async"
      >
      <span v-if="moment.images.length > 3" class="moment-image-strip__more">
        +{{ moment.images.length - 3 }}
      </span>
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
  flex: 1;
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

.moment-like-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
}

.moment-like-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  min-height: 32px;
  padding: 0;
  border-radius: 10px;
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.08);
}

.moment-like-btn:hover {
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.14);
}

.moment-like-btn :deep(svg) {
  font-size: 18px;
}

.moment-like-count {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1;
}

.moment-image-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  overflow-x: auto;
}

.moment-image-strip img,
.moment-image-strip__more {
  width: 72px;
  height: 72px;
  border-radius: 14px;
  object-fit: cover;
  flex: 0 0 auto;
}

.moment-image-strip__more {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--el-color-primary-light-8) 62%, transparent);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.dark .moment-like-btn {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .moment-like-btn:hover {
  color: #fff;
  background: rgba(var(--el-color-primary-rgb), 0.22);
}

@media (max-width: 576px) {
  .moment-card {
    padding: 14px;
  }

}
</style>
