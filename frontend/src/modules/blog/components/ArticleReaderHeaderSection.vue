<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { ElButton } from 'element-plus'
import { computed } from 'vue'
import SegmentedSwitch from '../../../shared/components/SegmentedSwitch.vue'
import ArticleCoverImage from '../../articles/components/ArticleCoverImage.vue'
import type { ArticleRecord } from '../../articles/types'
import { sponsorConfig } from '../constants/sponsorConfig'
import ArticleMeta from './ArticleMeta.vue'
import SharePoster from './SharePoster.vue'

const props = defineProps<{
  article: ArticleRecord
  readingTimeInfo: { minutes: number; words: number } | null
  articleViewMode: 'markdown' | 'mindmap'
  articleViewModeOptions: readonly { label: string; value: 'markdown' | 'mindmap' }[]
  articleCoverImage: string | null
  articleUrl: string
  siteTitle: string
  articleLiking: boolean
}>()

const emit = defineEmits<{
  tagClick: [name: string]
  like: []
  sponsor: []
  'update:articleViewMode': [value: 'markdown' | 'mindmap']
}>()

const authorName = computed(() => props.article.author.nickname || props.article.author.username)

const articleViewModeModel = computed({
  get: () => props.articleViewMode,
  set: (value: 'markdown' | 'mindmap') => emit('update:articleViewMode', value),
})
</script>

<template>
  <div class="post-header">
    <div class="post-header-top">
      <div class="header-top-item">
        <span class="header-top-icon">
          <Icon icon="material-symbols:person-outline-rounded" class="header-top-icon-svg" />
        </span>
        <span>{{ authorName }}</span>
      </div>
      <div v-if="typeof article.view_count === 'number'" class="header-top-item">
        <span class="header-top-icon">
          <Icon icon="material-symbols:visibility-outline-rounded" class="header-top-icon-svg" />
        </span>
        <span>{{ article.view_count }} 次阅读</span>
      </div>
      <div v-if="readingTimeInfo" class="header-top-item">
        <span class="header-top-icon">
          <Icon icon="material-symbols:schedule-outline-rounded" class="header-top-icon-svg" />
        </span>
        <span>约 {{ readingTimeInfo.minutes }} 分钟 · {{ readingTimeInfo.words }} 字</span>
      </div>
    </div>

    <div class="post-title">{{ article.title }}</div>

    <ArticleMeta
      :published-at="article.published_at || article.created_at"
      :updated-at="article.last_edited_at || article.updated_at"
      :category="article.category"
      :tags="article.tags"
      @tag-click="emit('tagClick', $event)"
    />

    <div class="post-actions-bar">
      <div class="post-actions-left">
        <SharePoster
          :title="article.title"
          :author="authorName"
          :description="article.excerpt || ''"
          :pub-date="article.published_at || article.created_at"
          :cover-image="articleCoverImage"
          :url="articleUrl"
          :site-title="siteTitle"
          avatar="/头像.avif"
        />
        <ElButton
          v-if="sponsorConfig.showButtonInPost"
          size="small"
          class="sponsor-btn"
          aria-label="赞助支持"
          title="赞助支持"
          @click="emit('sponsor')"
        >
          <Icon icon="material-symbols:local-cafe-outline-rounded" class="sponsor-btn-icon" />
        </ElButton>
        <ElButton
          size="small"
          class="like-btn"
          :loading="articleLiking"
          aria-label="点赞文章"
          title="点赞文章"
          @click="emit('like')"
        >
          <Icon icon="material-symbols:favorite-outline-rounded" class="like-btn-icon" />
          <span class="like-btn-count">{{ article.like_count }}</span>
        </ElButton>
      </div>
      <div class="article-view-switch">
        <SegmentedSwitch
          v-model="articleViewModeModel"
          aria-label="文章查看模式"
          :options="articleViewModeOptions"
          active-color="var(--el-color-primary)"
          size="small"
        />
      </div>
    </div>

    <div v-if="article.cover_url" class="post-cover">
      <ArticleCoverImage :url="article.cover_url" :alt="article.title" preview />
    </div>
  </div>
</template>

<style scoped>
.post-header {
  padding: 1.5rem 1.5rem 1rem;
  border-radius: var(--radius-large);
  background: var(--card-bg-transparent);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  background-color: rgba(255, 255, 255, var(--overlay-card-opacity)) !important;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

@media (min-width: 768px) {
  .post-header {
    padding: 1.5rem 2.25rem 1rem;
  }
}

.dark .post-header {
  border-color: rgba(148, 163, 184, 0.16);
  background-color: rgba(15, 23, 42, var(--overlay-card-opacity)) !important;
}

.post-header-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1.25rem;
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.3);
  margin-bottom: 0.75rem;
}

.dark .post-header-top {
  color: rgba(255, 255, 255, 0.3);
}

.header-top-item {
  display: inline-flex;
  align-items: center;
  line-height: 1.25rem;
}

.header-top-icon {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 0.375rem;
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.5);
  margin-right: 0.5rem;
}

.header-top-icon-svg {
  display: block;
  width: 0.875rem;
  height: 0.875rem;
}

.header-top-item > span {
  font-size: 0.875rem;
}

.dark .header-top-icon {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
}

.post-title {
  position: relative;
  font-size: 1.875rem;
  font-weight: 700;
  line-height: 1.35;
  margin: 0 0 0.75rem;
  color: var(--text-primary);
}

@media (min-width: 768px) {
  .post-title {
    font-size: 2.25rem;
    line-height: 2.75rem;
  }

  .post-title::before {
    content: '';
    position: absolute;
    top: 0.75rem;
    left: -1.125rem;
    width: 0.25rem;
    height: 1.25rem;
    border-radius: 0.375rem;
    background-color: var(--el-color-primary);
  }
}

.post-cover {
  margin-top: 1rem;
  border-radius: var(--radius-large);
  overflow: hidden;
}

.post-cover :deep(img) {
  width: 100%;
  max-height: 360px;
  object-fit: cover;
  display: block;
}

.post-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding-top: 0.75rem;
  margin-top: 0.75rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.dark .post-actions-bar {
  border-top-color: rgba(255, 255, 255, 0.08);
}

.post-actions-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  flex-wrap: wrap;
}

.sponsor-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  color: var(--el-color-primary);
  border: none;
  border-radius: 0.375rem;
  background: rgba(var(--el-color-primary-rgb), 0.1);
  transition: color var(--transition-base) ease, background-color var(--transition-base) ease, transform var(--transition-base) ease;
}

.like-btn {
  display: inline-flex;
  align-items: center;
  padding: 0 0.75rem 0 0.625rem;
  min-height: 2rem;
  color: var(--el-color-primary);
  border: none;
  border-radius: 0.375rem;
  background: rgba(var(--el-color-primary-rgb), 0.1);
  transition: color var(--transition-base) ease, background-color var(--transition-base) ease, transform var(--transition-base) ease;
}

.like-btn:hover,
.sponsor-btn:hover {
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .sponsor-btn {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .like-btn {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(var(--el-color-primary-rgb), 0.16);
}

.dark .like-btn:hover,
.dark .sponsor-btn:hover {
  color: #fff;
  background: rgba(var(--el-color-primary-rgb), 0.22);
}

.like-btn-icon,
.sponsor-btn-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.like-btn-count {
  margin-left: 0.45rem;
}

@media (max-width: 576px) {
  .post-title {
    font-size: 1.375rem;
  }
}
</style>
