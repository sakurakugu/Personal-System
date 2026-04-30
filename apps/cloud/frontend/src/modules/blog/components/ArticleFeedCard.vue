<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed } from 'vue'
import type { FeedArticleRecord } from '../../../modules/feed/types'
import ArticleCoverImage from '../../articles/components/ArticleCoverImage.vue'

import type { ArticleRecord } from '../../../modules/articles/types'

const props = defineProps<{
  article: FeedArticleRecord | ArticleRecord
  highlightKeyword?: string
  layout?: 'list' | 'grid'
}>()

const emit = defineEmits<{
  (e: 'click', slug: string): void
  (e: 'tagClick', name: string): void
}>()

function handleClick() {
  emit('click', props.article.slug)
}

function handleTagClick(name: string) {
  emit('tagClick', name)
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    switch (char) {
      case '&': return '&amp;'
      case '<': return '&lt;'
      case '>': return '&gt;'
      case '"': return '&quot;'
      case '\'': return '&#39;'
      default: return char
    }
  })
}

const highlightedTitle = computed(() => {
  const keyword = (props.highlightKeyword || '').trim()
  const safeTitle = escapeHtml(props.article.title)
  if (!keyword) {
    return safeTitle
  }
  return safeTitle.replace(new RegExp(escapeRegExp(keyword), 'gi'), (match) => `<mark>${match}</mark>`)
})
</script>

<template>
  <div
    class="feed-card article-card"
    :class="[
      article.cover_url ? 'has-cover' : 'no-cover',
      layout === 'grid' ? 'is-grid' : '',
    ]"
  >
    <div class="article-content">
      <a class="article-title" @click.prevent="handleClick">
        <template v-if="highlightKeyword">
          <span v-html="highlightedTitle" />
        </template>
        <template v-else>
          {{ article.title }}
        </template>
      </a>
      <div class="article-meta">
        <div v-if="article.pinned" class="pinned-row">
          <span class="pinned-badge">
            <Icon icon="material-symbols:pinboard" />
            <span>置顶</span>
          </span>
        </div>
        <div class="meta-row">
          <span class="meta-item">
            <span class="meta-icon"><Icon icon="material-symbols:calendar-today-outline-rounded" /></span>
            <span class="meta-text">{{ new Date(article.published_at || article.created_at).toLocaleDateString() }}</span>
          </span>
          <span v-if="article.category" class="meta-item">
            <span class="meta-icon"><Icon icon="material-symbols:book-2-outline-rounded" /></span>
            <span class="meta-text">{{ article.category.name }}</span>
          </span>
          <span class="meta-item">
            <span class="meta-icon"><Icon icon="material-symbols:person-outline-rounded" /></span>
            <span class="meta-text">{{ article.author.nickname || article.author.username }}</span>
          </span>
          <span class="meta-item">
            <span class="meta-icon"><Icon icon="material-symbols:visibility-outline-rounded" /></span>
            <span class="meta-text">{{ article.view_count }}</span>
          </span>
          <span class="meta-item">
            <span class="meta-icon"><Icon icon="material-symbols:favorite-outline-rounded" /></span>
            <span class="meta-text">{{ article.like_count }}</span>
          </span>
        </div>
      </div>
      <p class="article-excerpt">{{ article.excerpt || '暂无摘要' }}</p>
      <div v-if="article.tags.length" class="tag-row">
        <span v-for="tag in article.tags" :key="tag.id" class="meta-tag" @click.stop="handleTagClick(tag.name)">#{{ tag.name }}</span>
      </div>
    </div>
    <a v-if="article.cover_url" class="article-cover" @click.prevent="handleClick">
      <div class="article-cover-mask" />
      <div class="article-cover-arrow">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z" />
        </svg>
      </div>
      <ArticleCoverImage :url="article.cover_url" :alt="article.title" />
    </a>
    <a v-else class="article-enter" @click.prevent="handleClick">
      <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
        <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z" />
      </svg>
    </a>
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

/* Article Card */
.article-card {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  position: relative;
  min-height: auto;
}

.article-card .article-content {
  position: relative;
  width: calc(100% - 30% - 1.5rem);
  min-width: 0;
  padding: 1.75rem 0.5rem 1.75rem 2.25rem;
  display: flex;
  flex-direction: column;
}

.article-card.no-cover .article-content {
  width: calc(100% - 52px - 12px);
}

.article-title {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 2rem;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
  text-decoration: none;
  transition: color 0.2s;
  cursor: pointer;
}

.article-title::before {
  content: '';
  position: absolute;
  left: 18px;
  top: 2.25rem;
  width: 4px;
  height: 1rem;
  border-radius: 2px;
  background: var(--primary);
}

.article-title:hover {
  color: var(--primary);
}

.article-meta {
  margin-bottom: 0.5rem;
}

.pinned-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.pinned-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: 6px;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
}

.pinned-badge svg {
  width: 1.25rem;
  height: 1.25rem;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  font-size: 16px;
  transition: background-color 0.15s, color 0.15s;
}

.meta-icon :deep(svg) {
  width: 1.25rem;
  height: 1.25rem;
}

.meta-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  transition: all 0.2s;
  cursor: pointer;
}

.meta-tag:hover {
  background: var(--btn-regular-bg-hover);
  color: var(--primary);
  transform: scale(1.05);
}

.meta-tag:active {
  transform: scale(0.95);
}

.article-excerpt {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-clamp: 2;
  margin-bottom: 12px;
  flex: 1;
}

.article-cover {
  position: absolute;
  top: 1rem;
  bottom: 1rem;
  right: 1rem;
  width: 30%;
  min-width: 180px;
  max-width: 320px;
  border-radius: 0.75rem;
  overflow: hidden;
  cursor: pointer;
}

.article-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.article-cover:hover img {
  transform: scale(1.1);
}

.article-cover-mask {
  position: absolute;
  inset: 0;
  z-index: 10;
  pointer-events: none;
  background: rgba(0, 0, 0, 0);
  transition: background 0.2s;
}

.article-cover:hover .article-cover-mask {
  background: rgba(0, 0, 0, 0.3);
}

.article-cover-arrow {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.article-cover-arrow svg {
  color: white;
  width: 3rem;
  height: 3rem;
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s;
}

.article-cover:hover .article-cover-arrow svg {
  opacity: 1;
  transform: scale(1);
}

.article-enter {
  position: absolute;
  right: 12px;
  top: 12px;
  bottom: 12px;
  width: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--enter-btn-bg);
  color: var(--primary);
  cursor: pointer;
  transition: background 0.2s;
  text-decoration: none;
  border-radius: 12px;
}

.article-enter:hover {
  background: var(--enter-btn-bg-hover);
}

.article-enter:active {
  transform: scale(0.95);
  background: var(--enter-btn-bg-active);
}

@media (max-width: 992px) {
  .article-card {
    flex-direction: row;
    min-height: auto;
  }

  .article-card .article-content,
  .article-card.no-cover .article-content {
    width: calc(100% - 9rem - 0.75rem);
    padding: 0.75rem 0.5rem 0.75rem 0.75rem;
  }

  .article-card.no-cover .article-content {
    width: calc(100% - 52px - 12px);
  }

  .article-cover {
    top: 0.5rem;
    bottom: 0.5rem;
    right: 0.5rem;
    width: 9rem;
    min-width: auto;
    max-width: none;
    aspect-ratio: auto;
  }

  .article-title {
    font-size: 1.125rem;
    line-height: 1.75rem;
    margin-bottom: 0.5rem;
  }

  .article-title::before {
    display: none;
  }

  .tag-row {
    gap: 0.25rem;
  }

  .meta-tag {
    font-size: 0.65rem;
    padding: 0.125rem 0.375rem;
    height: 1.25rem;
  }

  .article-enter {
    display: flex;
  }
}

@media (max-width: 576px) {
  .article-title {
    font-size: 1.125rem;
  }

  .article-title::before {
    display: none;
  }
}

/* ==================== Grid 布局样式 ==================== */
.article-card.is-grid {
  flex-direction: column-reverse;
  height: 100%;
}

.article-card.is-grid .article-content {
  width: 100%;
  padding: 1rem;
  flex-grow: 1;
}

.article-card.is-grid.no-cover .article-content {
  width: calc(100% - 52px - 12px);
}

.article-card.is-grid .article-cover {
  position: relative;
  top: auto;
  right: auto;
  bottom: auto;
  width: 100%;
  min-width: auto;
  max-width: none;
  aspect-ratio: 2 / 1;
  border-radius: var(--radius-large) var(--radius-large) 0 0;
  margin: 0;
}

.article-card.is-grid .article-cover img {
  border-radius: var(--radius-large) var(--radius-large) 0 0;
}

.article-card.is-grid .article-title {
  font-size: 1.25rem;
  line-height: 1.75rem;
  margin-bottom: 0.5rem;
}

.article-card.is-grid .article-title::before {
  display: none;
}

.article-card.is-grid .article-excerpt {
  flex: 0 0 auto;
}

.article-card.is-grid .tag-row {
  margin-top: auto;
}
</style>
