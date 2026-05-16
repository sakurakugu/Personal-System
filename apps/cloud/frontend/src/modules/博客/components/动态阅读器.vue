<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { ElButton, ElEmpty, ElMessage, ElSkeleton } from 'element-plus'
import axios from 'axios'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchPublicMomentById, likeMoment, recordMomentView, unlikeMoment } from '@personal-system/module-moments'
import type { PublishedMoment } from '@personal-system/module-moments'
import MarkdownRenderer from '@personal-system/module-articles/components/Markdown渲染器.vue'
import { useSettingsStore } from '../../../shared/stores/settings'
import TwikooPanel from './评论面板.vue'
import { resolveManagedFileUrl } from '../../../shared/utils/managedFile'

const props = defineProps<{
  momentId: string
}>()

const route = useRoute()
const router = useRouter()
const settings = useSettingsStore()

const loading = ref(false)
const likeLoading = ref(false)
const moment = ref<PublishedMoment | null>(null)
const loadErrorStatus = ref<number | null>(null)

const commentsPath = computed(() => {
  const id = props.momentId.trim()
  return id ? `/moments/${id}` : '/moments'
})

async function loadMoment(id: string) {
  if (!id) {
    moment.value = null
    loadErrorStatus.value = null
    return
  }

  loading.value = true
  moment.value = null
  loadErrorStatus.value = null

  try {
    const data = await fetchPublicMomentById(id)
    moment.value = data

    const viewResult = await recordMomentView(id)
    moment.value = {
      ...data,
      view_count: viewResult.view_count,
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      loadErrorStatus.value = error.response?.status ?? null
    } else {
      loadErrorStatus.value = 500
    }
  } finally {
    loading.value = false
  }
}

async function handleLike() {
  if (!moment.value || likeLoading.value) return

  likeLoading.value = true
  try {
    const result = moment.value.liked
      ? await unlikeMoment(moment.value.id)
      : await likeMoment(moment.value.id)
    moment.value = {
      ...moment.value,
      like_count: result.like_count,
      liked: result.liked,
    }
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

function formatDateTime(date: string | null) {
  if (!date) return '刚刚'
  return new Date(date).toLocaleString('zh-CN')
}

function getEditedTooltip(publishedAt: string | null, lastEditedAt: string) {
  if (!publishedAt) return ''
  if (new Date(lastEditedAt).getTime() <= new Date(publishedAt).getTime()) {
    return ''
  }
  return `编辑于 ${formatDateTime(lastEditedAt)}`
}

function getMomentImageUrl(url: string) {
  return resolveManagedFileUrl(url)
}

function showLoginModal() {
  void router.replace({ query: { ...route.query, login: '1' } })
}

watch(
  () => props.momentId,
  (id) => {
    void loadMoment(id)
  },
  { immediate: true },
)
</script>

<template>
  <div class="moment-reader">
    <ElSkeleton :loading="loading" animated>
      <template v-if="moment">
        <div class="moment-detail-card">
          <div class="moment-detail-header">
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
                <span :title="getEditedTooltip(moment.published_at, moment.last_edited_at) || undefined">
                  {{ formatDateTime(moment.published_at) }}
                </span>
              </div>
            </div>
            <div class="moment-stats">
              <span class="moment-stat">
                <Icon icon="material-symbols:visibility-outline-rounded" />
                <span>{{ moment.view_count }}</span>
              </span>
            </div>
          </div>

          <h1 v-if="moment.title" class="moment-title">{{ moment.title }}</h1>

          <hr class="moment-section-divider">

          <div class="moment-content">
            <MarkdownRenderer class="article-markdown-preview" :content="moment.content" />
          </div>

          <div v-if="moment.images.length > 0" class="moment-image-grid">
            <img
              v-for="image in moment.images"
              :key="image.id"
              :src="getMomentImageUrl(image.preview_url || image.url)"
              :alt="image.original_name"
              class="moment-image-grid__item"
              loading="lazy"
              decoding="async"
            >
          </div>

          <div class="moment-actions">
            <div class="moment-like-group">
              <ElButton
                size="small"
                text
                class="moment-like-btn"
                :loading="likeLoading"
                :aria-label="moment.liked ? '取消点赞' : '点赞'"
                :title="moment.liked ? '取消点赞' : '点赞'"
                @click="handleLike"
              >
                <Icon :icon="moment.liked ? 'material-symbols:favorite-rounded' : 'material-symbols:favorite-outline-rounded'" />
              </ElButton>
              <span class="moment-like-count">{{ moment.like_count }}</span>
            </div>
          </div>
        </div>

        <TwikooPanel
          :path="commentsPath"
          :hide-admin-entry="true"
          :visibility="settings.commentVisibility"
        />
      </template>

      <ElEmpty v-else-if="!loading && loadErrorStatus === 401" description="该动态需要登录后查看">
        <ElButton type="primary" @click="showLoginModal">立即登录</ElButton>
      </ElEmpty>
      <ElEmpty v-else-if="!loading" description="动态不存在" />
    </ElSkeleton>
  </div>
</template>

<style scoped>
.moment-reader {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.moment-detail-card {
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
}

.dark .moment-detail-card {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.moment-detail-card {
  padding: 1.5rem;
}

.moment-detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
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
  width: 48px;
  height: 48px;
  overflow: hidden;
  border-radius: 50%;
  background: var(--theme-accent-gradient);
  color: #fff;
  font-weight: 700;
  flex: 0 0 auto;
}

.moment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.moment-author-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.moment-author-meta strong {
  color: var(--text-primary);
  font-size: 15px;
}

.moment-author-meta span {
  color: var(--text-tertiary);
  font-size: 13px;
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
  color: var(--text-secondary);
  font-size: 14px;
}

.moment-stat :deep(svg) {
  font-size: 18px;
}

.moment-title {
  margin: 1rem 0 0;
  font-size: 1.9rem;
  line-height: 1.35;
  color: var(--text-primary);
}

.moment-section-divider {
  margin: 1.25rem 0;
  border: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.dark .moment-section-divider {
  border-top-color: rgba(255, 255, 255, 0.1);
}

.moment-content :deep(.article-markdown-preview) {
  width: 100%;
}

.moment-actions {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 12px;
}

.moment-image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 1rem;
}

.moment-image-grid__item {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 16px;
  object-fit: cover;
  background: var(--el-fill-color-light);
}

.moment-like-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.moment-like-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  min-height: 32px;
  padding: 0;
  color: var(--el-color-primary);
  border-radius: 10px;
  background: rgba(var(--el-color-primary-rgb), 0.08);
}

.moment-like-btn:hover {
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.14);
}

.dark .moment-like-btn {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .moment-like-btn:hover {
  color: #fff;
  background: rgba(var(--el-color-primary-rgb), 0.22);
}

.moment-like-btn :deep(svg) {
  font-size: 18px;
}

.moment-like-count {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1;
}

@media (max-width: 576px) {
  .moment-detail-card {
    padding: 1.1rem;
  }

  .moment-detail-header {
    flex-direction: column;
  }

  .moment-title {
    font-size: 1.45rem;
  }
}
</style>
