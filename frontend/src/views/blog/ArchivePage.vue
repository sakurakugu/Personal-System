<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchAllArticleMeta } from '../../features/articles/api'
import type { ArticleMetaRecord } from '../../features/articles/types'

const route = useRoute()
const router = useRouter()

const articles = ref<ArticleMetaRecord[]>([])
const loading = ref(true)

const categoryFilter = computed(() => {
  const c = route.query.category
  return typeof c === 'string' ? c : null
})

const tagFilter = computed(() => {
  const t = route.query.tag
  return typeof t === 'string' ? t : null
})

const uncategorizedFilter = computed(() => {
  return route.query.uncategorized !== undefined
})

const filteredArticles = computed(() => {
  let list = articles.value.slice()

  if (tagFilter.value) {
    list = list.filter(a => a.tags.some(tag => tag.slug === tagFilter.value || tag.name === tagFilter.value))
  }

  if (categoryFilter.value) {
    list = list.filter(a => a.category?.slug === categoryFilter.value || a.category?.name === categoryFilter.value)
  }

  if (uncategorizedFilter.value) {
    list = list.filter(a => !a.category)
  }

  // 按发布时间倒序
  return list.sort((a, b) => {
    const ta = a.published_at ? new Date(a.published_at).getTime() : 0
    const tb = b.published_at ? new Date(b.published_at).getTime() : 0
    return tb - ta
  })
})

interface YearGroup {
  year: number
  posts: ArticleMetaRecord[]
}

const groups = computed<YearGroup[]>(() => {
  const map: Record<number, ArticleMetaRecord[]> = {}
  filteredArticles.value.forEach(post => {
    if (!post.published_at) return
    const year = new Date(post.published_at).getFullYear()
    if (!map[year]) map[year] = []
    map[year].push(post)
  })
  return Object.keys(map)
    .map(y => ({ year: Number(y), posts: map[Number(y)] }))
    .sort((a, b) => b.year - a.year)
})

const hasFilters = computed(() => {
  return categoryFilter.value || tagFilter.value || uncategorizedFilter.value
})

const filterSummary = computed(() => {
  const parts: string[] = []
  if (categoryFilter.value) parts.push(`分类: ${categoryFilter.value}`)
  if (tagFilter.value) parts.push(`标签: #${tagFilter.value}`)
  if (uncategorizedFilter.value) parts.push('分类: 未分类')
  return parts.join(' · ')
})

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

function formatTags(tags: ArticleMetaRecord['tags']) {
  return tags.map(t => `#${t.name}`).join(' ')
}

function goArticle(slug: string) {
  void router.push(`/blog/${slug}`)
}

function goBack() {
  void router.push('/blog')
}

function clearFilters() {
  void router.replace({ path: '/archive', query: {} })
}

onMounted(async () => {
  try {
    articles.value = await fetchAllArticleMeta()
  } catch {
    articles.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="archive-page">
    <div class="archive-container">
      <!-- 头部 -->
      <div class="archive-header">
        <button class="back-btn" @click="goBack">
          <span class="back-arrow">←</span>
          <span>返回</span>
        </button>
        <h1 class="archive-title">文章归档</h1>
        <div class="archive-stats">
          共 {{ filteredArticles.length }} 篇文章 · {{ groups.length }} 个年份
        </div>
      </div>

      <!-- 筛选摘要 -->
      <div v-if="hasFilters" class="filter-bar">
        <div class="filter-summary">
          <span class="filter-label">筛选条件</span>
          <span class="filter-value">{{ filterSummary }}</span>
        </div>
        <button class="filter-clear" @click="clearFilters">
          清除筛选
        </button>
      </div>

      <!-- 内容 -->
      <div v-loading="loading" class="archive-content">
        <div v-if="!loading && groups.length === 0" class="empty-state">
          暂无文章
        </div>

        <div
          v-for="group in groups"
          :key="group.year"
          class="year-group"
        >
          <!-- 年份标题 -->
          <div class="year-header">
            <div class="year-number">{{ group.year }}</div>
            <div class="year-dot" />
            <div class="year-count">{{ group.posts.length }} 篇文章</div>
          </div>

          <!-- 文章列表 -->
          <div class="post-list">
            <div
              v-for="post in group.posts"
              :key="post.id"
              class="post-item"
              @click="goArticle(post.slug)"
            >
              <div class="post-date">{{ formatDate(post.published_at!) }}</div>
              <div class="post-line">
                <div class="post-dot" />
              </div>
              <div class="post-title">{{ post.title }}</div>
              <div class="post-tags">{{ formatTags(post.tags) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.archive-page {
  min-height: calc(var(--app-viewport-height) - var(--app-header-height));
  padding: 24px 16px calc(32px + var(--app-safe-area-bottom));
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.5), transparent 42%),
    linear-gradient(180deg, oklch(0.96 0.008 var(--hue) / 0.86) 0%, oklch(0.96 0.008 var(--hue) / 0.96) 28%, oklch(0.96 0.008 var(--hue)) 100%);
}

.dark .archive-page {
  background:
    radial-gradient(circle at 18% 18%, oklch(0.75 0.08 var(--hue) / 0.15) 0%, transparent 26%),
    radial-gradient(circle at 82% 14%, oklch(0.80 0.06 var(--hue) / 0.12) 0%, transparent 20%),
    linear-gradient(180deg, oklch(0.19 0.018 var(--hue) / 0.2) 0%, oklch(0.19 0.018 var(--hue) / 0.8) 28%, oklch(0.19 0.018 var(--hue) / 0.96) 100%);
}

.archive-container {
  max-width: 900px;
  margin: 0 auto;
}

.archive-header {
  text-align: center;
  margin-bottom: 24px;
  position: relative;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
  color: var(--primary);
}

.archive-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.archive-stats {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  border-radius: 1rem;
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
}

.dark .filter-bar {
  background: rgba(15, 23, 42, 0.62);
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.filter-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 14px;
}

.filter-label {
  color: var(--text-tertiary);
}

.filter-value {
  color: var(--primary);
  font-weight: 600;
}

.filter-clear {
  padding: 4px 12px;
  border-radius: 8px;
  border: 1px solid var(--line-divider);
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.filter-clear:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* 内容卡片 */
.archive-content {
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  border-radius: 1rem;
  padding: 24px 32px;
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
}

.dark .archive-content {
  background: rgba(15, 23, 42, 0.62);
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  font-size: 14px;
}

.year-group + .year-group {
  margin-top: 24px;
}

/* 年份标题 */
.year-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 3.75rem;
}

.year-number {
  width: 15%;
  text-align: right;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.year-dot {
  width: 15%;
  display: flex;
  justify-content: center;
}

.year-dot::before {
  content: '';
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 9999px;
  background: transparent;
  outline: 3px solid var(--primary);
  outline-offset: -2px;
}

.year-count {
  width: 70%;
  text-align: left;
  color: var(--text-secondary);
  font-size: 14px;
  transition: color 0.2s;
}

@media (min-width: 768px) {
  .year-number {
    width: 10%;
  }
  .year-dot {
    width: 10%;
  }
  .year-count {
    width: 80%;
  }
}

/* 文章项 */
.post-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  height: 2.5rem;
  width: 100%;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.post-item:hover {
  background: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
}

.post-item:hover .post-title {
  color: var(--primary);
  transform: translateX(4px);
}

.post-item:hover .post-dot {
  height: 1.25rem;
  background: var(--primary);
}

.post-item:hover .post-dot {
  outline-color: var(--btn-plain-bg-hover, rgba(0, 0, 0, 0.05));
}

.post-date {
  width: 15%;
  text-align: right;
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.post-line {
  width: 15%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.post-line::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  background: repeating-linear-gradient(
    to bottom,
    var(--line-divider) 0,
    var(--line-divider) 4px,
    transparent 4px,
    transparent 8px
  );
  transform: translateX(-50%);
}

.year-group:first-of-type .post-list .post-item:first-child .post-line::before {
  top: 50%;
}

.year-group:last-of-type .post-list .post-item:last-child .post-line::before {
  bottom: 50%;
}

.post-dot {
  width: 0.25rem;
  height: 0.25rem;
  border-radius: 9999px;
  background: oklch(0.5 0.05 var(--hue));
  outline: 4px solid rgba(255, 255, 255, 0.68);
  z-index: 10;
  transition: all 0.2s;
}

.dark .post-dot {
  outline-color: rgba(15, 23, 42, 0.62);
}

.post-title {
  width: 70%;
  padding-right: 2rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s;
}

.post-tags {
  display: none;
}

@media (min-width: 768px) {
  .post-date {
    width: 10%;
  }
  .post-line {
    width: 10%;
  }
  .post-title {
    width: 65%;
    padding-right: 2rem;
  }
  .post-tags {
    display: block;
    width: 15%;
    text-align: left;
    font-size: 0.875rem;
    color: var(--text-tertiary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: color 0.2s;
  }
  .post-item:hover .post-tags {
    color: var(--primary);
  }
}

@media (max-width: 640px) {
  .archive-content {
    padding: 16px 20px;
  }
  .archive-title {
    font-size: 1.5rem;
  }
  .back-btn {
    position: static;
    transform: none;
    margin-bottom: 12px;
  }
  .archive-header {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
}
</style>
