<script setup lang="ts">
/* global fetch */
import { Icon } from '@iconify/vue'
import { ElEmpty, ElSkeleton } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { bangumiConfig, type BangumiCategoryConfig, type BangumiCategoryId } from '../constants/bangumiConfig'

interface BangumiSubject {
  id: number
  name: string
  name_cn?: string
  date?: string
  eps?: number
  score?: number
  type?: number
  images?: {
    small?: string
    grid?: string
    large?: string
    common?: string
    medium?: string
  }
  tags?: Array<{ name: string }>
  short_summary?: string
}

interface BangumiCollectionItem {
  subject_id: number
  type: number
  rate?: number
  comment?: string
  updated_at?: string
  tags?: string[]
  subject: BangumiSubject
}

interface BangumiCollectionResponse {
  data?: BangumiCollectionItem[]
  total?: number
  limit?: number
  offset?: number
}

interface FilterConfig {
  value: string
  label: string
  count?: number
}

const enabledCategories = computed(() => bangumiConfig.categories.filter(category => category.enabled))
const activeTab = ref<BangumiCategoryId | ''>('')
const loading = ref(false)
const errorMessage = ref('')
const dataMap = reactive<Record<BangumiCategoryId, BangumiCollectionItem[]>>({
  anime: [],
  book: [],
  music: [],
  game: [],
  real: [],
})

const filterMap = reactive<Record<BangumiCategoryId, string>>({
  anime: 'all',
  book: 'all',
  music: 'all',
  game: 'all',
  real: 'all',
})

const pageMap = reactive<Record<BangumiCategoryId, number>>({
  anime: 1,
  book: 1,
  music: 1,
  game: 1,
  real: 1,
})

const itemsPerPage = 12

const isUserConfigured = computed(() => bangumiConfig.userId.trim().length > 0)

const statusMap: Record<number, string> = {
  1: 'wish',
  2: 'collect',
  3: 'doing',
  4: 'on_hold',
  5: 'dropped',
}

const statusColorMap: Record<number, string> = {
  1: 'bg-blue-500',
  2: 'bg-green-500',
  3: 'bg-yellow-500',
  4: 'bg-orange-500',
  5: 'bg-red-500',
}

function getCoverUrl(item: BangumiCollectionItem) {
  return item.subject.images?.medium
    || item.subject.images?.common
    || item.subject.images?.large
    || item.subject.images?.grid
    || item.subject.images?.small
    || ''
}

function getStatusText(type: number, subjectType?: number) {
  switch (type) {
    case 1:
      if (subjectType === 1) return '想读'
      if (subjectType === 3) return '想听'
      if (subjectType === 4) return '想玩'
      return '想看'
    case 2:
      if (subjectType === 1) return '读过'
      if (subjectType === 3) return '听过'
      if (subjectType === 4) return '玩过'
      return '看过'
    case 3:
      if (subjectType === 1) return '在读'
      if (subjectType === 3) return '在听'
      if (subjectType === 4) return '在玩'
      return '在看'
    case 4:
      return '搁置'
    case 5:
      return '抛弃'
    default:
      return '未知'
  }
}

async function fetchCategoryData(category: BangumiCategoryConfig) {
  const limit = bangumiConfig.requestLimit
  const delay = 50
  const maxTotal = 1000
  let offset = 0
  let allData: BangumiCollectionItem[] = []
  let hasMore = true

  while (hasMore) {
    if (maxTotal > 0 && allData.length >= maxTotal) {
      break
    }

    const url = `/api/v1/bangumi/collections?username=${encodeURIComponent(bangumiConfig.userId)}&subject_type=${category.subjectType}&limit=${limit}&offset=${offset}`

    const response = await fetch(url, {
      headers: {
        Accept: 'application/json',
      },
    })

    if (!response.ok) {
      console.warn(`[Bangumi] 无法获取数据 (状态码: ${response.status}):`, url)
      break
    }

    const data = await response.json() as BangumiCollectionResponse
    const currentBatch = data.data || []

    if (currentBatch.length > 0) {
      allData = allData.concat(currentBatch)
      offset += limit
      if (currentBatch.length < limit) {
        hasMore = false
      }
    } else {
      hasMore = false
    }

    if (hasMore) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  dataMap[category.id] = allData
}

async function loadBangumiData() {
  if (!isUserConfigured.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const categories = enabledCategories.value
    await Promise.all(categories.map(category => fetchCategoryData(category)))
  } catch {
    errorMessage.value = 'Bangumi 数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

const filteredItems = computed(() => {
  if (!activeTab.value) return []
  const items = dataMap[activeTab.value]
  const filter = filterMap[activeTab.value]
  if (filter === 'all') return items
  return items.filter(item => statusMap[item.type] === filter)
})

const paginatedItems = computed(() => {
  if (!activeTab.value) return []
  const page = pageMap[activeTab.value]
  const start = (page - 1) * itemsPerPage
  return filteredItems.value.slice(start, start + itemsPerPage)
})

const totalPages = computed(() => {
  if (!activeTab.value) return 0
  return Math.ceil(filteredItems.value.length / itemsPerPage)
})

function getFilters(categoryId: BangumiCategoryId): FilterConfig[] {
  const items = dataMap[categoryId]
  const counts = items.reduce((acc, item) => {
    const status = statusMap[item.type] || 'unknown'
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const isGame = categoryId === 'game'
  const isBook = categoryId === 'book'
  const isMusic = categoryId === 'music'

  const getLabel = (type: 'collect' | 'doing' | 'wish') => {
    if (isGame) {
      if (type === 'collect') return '玩过'
      if (type === 'doing') return '在玩'
      return '想玩'
    }
    if (isBook) {
      if (type === 'collect') return '读过'
      if (type === 'doing') return '在读'
      return '想读'
    }
    if (isMusic) {
      if (type === 'collect') return '听过'
      if (type === 'doing') return '在听'
      return '想听'
    }
    if (type === 'collect') return '看过'
    if (type === 'doing') return '在看'
    return '想看'
  }

  const filters: FilterConfig[] = [
    { value: 'all', label: '全部', count: items.length },
    { value: 'collect', label: getLabel('collect'), count: counts.collect || 0 },
    { value: 'doing', label: getLabel('doing'), count: counts.doing || 0 },
    { value: 'wish', label: getLabel('wish'), count: counts.wish || 0 },
    { value: 'on_hold', label: '搁置', count: counts.on_hold || 0 },
    { value: 'dropped', label: '抛弃', count: counts.dropped || 0 },
  ]

  return filters.filter(f => f.value === 'all' || (f.count && f.count > 0))
}

function setFilter(filter: string) {
  if (!activeTab.value) return
  filterMap[activeTab.value] = filter
  pageMap[activeTab.value] = 1
}

function setTab(tabId: BangumiCategoryId) {
  activeTab.value = tabId
}

function setPage(page: number) {
  if (!activeTab.value) return
  pageMap[activeTab.value] = page
}

function goPrev() {
  if (!activeTab.value) return
  if (pageMap[activeTab.value] > 1) {
    pageMap[activeTab.value]--
  }
}

function goNext() {
  if (!activeTab.value) return
  if (pageMap[activeTab.value] < totalPages.value) {
    pageMap[activeTab.value]++
  }
}

function generatePageNumbers(current: number, total: number): (number | string)[] {
  const delta = 2
  const rangeWithDots: (number | string)[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      rangeWithDots.push(i)
    }
    return rangeWithDots
  }

  const left = Math.max(2, current - delta)
  const right = Math.min(total - 1, current + delta)

  rangeWithDots.push(1)
  if (left > 2) {
    rangeWithDots.push('...')
  }
  for (let i = left; i <= right; i++) {
    rangeWithDots.push(i)
  }
  if (right < total - 1) {
    rangeWithDots.push('...')
  }
  if (total > 1) {
    rangeWithDots.push(total)
  }

  return rangeWithDots
}

const pageNumbers = computed(() => {
  if (!activeTab.value) return []
  return generatePageNumbers(pageMap[activeTab.value], totalPages.value)
})

watch(activeTab, () => {
  // 当切换标签时，重置页码到第一页
  if (activeTab.value) {
    pageMap[activeTab.value] = 1
  }
})

onMounted(async () => {
  activeTab.value = enabledCategories.value[0]?.id || ''
  await loadBangumiData()
})
</script>

<template>
  <div class="bangumi-view">
    <div class="bangumi-card">
      <!-- 页面标题 -->
      <div class="bangumi-header">
        <div class="bangumi-title-wrap">
          <div class="bangumi-title-icon">
            <Icon icon="material-symbols:movie" />
          </div>
          <div>
            <h1 class="bangumi-title">追番记录</h1>
            <p class="bangumi-subtitle">同步 Bangumi 个人收藏，集中展示动画、书籍、音乐与游戏记录。</p>
          </div>
        </div>
      </div>

      <div v-if="!isUserConfigured" class="bangumi-empty-wrap">
        <ElEmpty description="尚未配置 Bangumi 用户名">
          <template #description>
            <p class="bangumi-empty-text">请在 src/modules/blog/constants/bangumiConfig.ts 中填写 userId 后刷新页面。</p>
          </template>
        </ElEmpty>
      </div>

      <template v-else>
        <!-- Tab 导航 -->
        <div v-if="enabledCategories.length > 0" class="bangumi-tabs" role="tablist" aria-label="Bangumi 分类">
          <div class="bangumi-tabs-scroll">
            <nav class="bangumi-tabs-nav">
              <button
                v-for="tab in enabledCategories"
                :key="tab.id"
                type="button"
                class="bangumi-tab"
                :class="{ active: activeTab === tab.id }"
                role="tab"
                :aria-selected="activeTab === tab.id"
                @click="setTab(tab.id)"
              >
                {{ tab.name }}
                <span class="tab-count">{{ dataMap[tab.id].length }}</span>
              </button>
            </nav>
          </div>
        </div>

        <!-- 内容区域 -->
        <div v-for="tab in enabledCategories" :key="tab.id" class="bangumi-section" :class="{ hidden: activeTab !== tab.id }" :data-section="tab.id">
          <div v-if="loading" class="bangumi-loading">
            <ElSkeleton :rows="8" animated />
          </div>

          <div v-else-if="errorMessage" class="bangumi-empty-wrap">
            <ElEmpty :description="errorMessage" />
          </div>

          <template v-else>
            <div v-if="dataMap[tab.id].length === 0" class="bangumi-empty-wrap">
              <ElEmpty description="当前分类暂无数据" />
            </div>

            <template v-else>
              <!-- 筛选器 -->
              <div class="filter-controls">
                <button
                  v-for="filter in getFilters(tab.id)"
                  :key="filter.value"
                  type="button"
                  class="filter-btn"
                  :class="{ active: filterMap[tab.id] === filter.value }"
                  @click="setFilter(filter.value)"
                >
                  {{ filter.label }}
                  <span v-if="filter.count !== undefined" class="filter-count">({{ filter.count }})</span>
                </button>
              </div>

              <!-- 卡片网格 -->
              <div class="bangumi-masonry">
                <a
                  v-for="item in (activeTab === tab.id ? paginatedItems : [])"
                  :key="item.subject_id"
                  :href="`https://bgm.tv/subject/${item.subject.id}`"
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  class="bangumi-item-card"
                >
                  <div class="card-cover-wrap">
                    <img
                      v-if="getCoverUrl(item)"
                      :src="getCoverUrl(item)"
                      :alt="item.subject.name_cn || item.subject.name"
                      class="card-cover"
                      loading="lazy"
                      decoding="async"
                    >
                    <div v-else class="card-cover-placeholder">
                      <span class="placeholder-icon">📖</span>
                    </div>

                    <!-- 状态徽章 -->
                    <div class="status-badge" :class="statusColorMap[item.type] || 'bg-gray-500'">
                      {{ getStatusText(item.type, item.subject.type) }}
                    </div>

                    <!-- 评分徽章 -->
                    <div v-if="item.subject.score" class="score-badge">
                      <span class="score-star">⭐</span>
                      {{ item.subject.score }}
                    </div>

                    <!-- 渐变遮罩 + 信息 -->
                    <div class="card-overlay" />
                    <div class="card-info">
                      <h3 class="card-title" :title="item.subject.name_cn || item.subject.name">
                        {{ item.subject.name_cn || item.subject.name }}
                      </h3>
                      <p v-if="item.subject.date" class="card-year">
                        {{ item.subject.date.substring(0, 4) }}
                      </p>
                      <p v-if="item.comment" class="card-comment" :title="item.comment">
                        {{ item.comment }}
                      </p>
                      <div v-if="(item.tags && item.tags.length > 0) || (item.subject.tags && item.subject.tags.length > 0)" class="card-tags">
                        <span
                          v-for="tag in (item.tags && item.tags.length > 0 ? item.tags : item.subject.tags!.map(t => t.name)).slice(0, 3)"
                          :key="tag"
                          class="card-tag"
                        >
                          {{ tag }}
                        </span>
                        <span v-if="(item.tags && item.tags.length > 0 ? item.tags : item.subject.tags!.map(t => t.name)).length > 3" class="card-tag tag-more">
                          +{{ (item.tags && item.tags.length > 0 ? item.tags : item.subject.tags!.map(t => t.name)).length - 3 }}
                        </span>
                      </div>
                    </div>
                  </div>
                </a>
              </div>

              <!-- 分页 -->
              <div v-if="activeTab === tab.id && totalPages > 1" class="pagination-root">
                <div class="pagination-inner" role="navigation" aria-label="分页">
                  <button
                    type="button"
                    class="nav-btn"
                    :class="{ disabled: pageMap[tab.id] === 1 }"
                    aria-label="上一页"
                    :disabled="pageMap[tab.id] === 1"
                    @click="goPrev"
                  >
                    <Icon icon="material-symbols:chevron-left-rounded" class="nav-icon" aria-hidden="true" />
                  </button>

                  <div class="page-numbers">
                    <div
                      class="active-slider"
                      :style="{ transform: `translateX(${pageNumbers.findIndex(p => p === pageMap[tab.id]) * 2.75}rem)` }"
                    />
                    <template v-for="(p, idx) in pageNumbers" :key="`${p}-${idx}`">
                      <span v-if="p === '...'" class="ellipsis" aria-hidden="true">
                        <Icon icon="material-symbols:more-horiz" />
                      </span>
                      <div
                        v-else-if="p === pageMap[tab.id]"
                        class="page-item page-current"
                        aria-current="page"
                      >
                        {{ p }}
                      </div>
                      <button
                        v-else
                        type="button"
                        class="page-item page-btn"
                        :aria-label="`第 ${p} 页`"
                        @click="setPage(p as number)"
                      >
                        {{ p }}
                      </button>
                    </template>
                  </div>

                  <button
                    type="button"
                    class="nav-btn"
                    :class="{ disabled: pageMap[tab.id] === totalPages }"
                    aria-label="下一页"
                    :disabled="pageMap[tab.id] === totalPages"
                    @click="goNext"
                  >
                    <Icon icon="material-symbols:chevron-right-rounded" class="nav-icon" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </template>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.bangumi-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bangumi-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
  padding: 24px 28px;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
}

.dark .bangumi-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.bangumi-header {
  margin-bottom: 16px;
}

.bangumi-title-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.bangumi-title-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--primary);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}

.dark .bangumi-title-icon {
  color: rgba(0, 0, 0, 0.75);
}

.bangumi-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.6rem;
  line-height: 1.3;
}

.bangumi-subtitle {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.95rem;
}

/* Tabs */
.bangumi-tabs {
  border-bottom: 1px solid var(--line-divider);
  margin-bottom: 12px;
}

.bangumi-tabs-scroll {
  overflow-x: auto;
}

.bangumi-tabs-nav {
  display: flex;
  min-width: max-content;
  gap: 2rem;
}

.bangumi-tab {
  position: relative;
  white-space: nowrap;
  padding: 12px 4px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.bangumi-tab:hover {
  color: var(--text-primary);
  border-bottom-color: var(--line-divider);
}

.bangumi-tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.tab-count {
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 0.7rem;
}

/* Section */
.bangumi-section.hidden {
  display: none;
}

/* Filter Controls */
.filter-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.filter-btn {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
}

.filter-btn:hover {
  background: var(--btn-regular-bg-hover);
}

.filter-btn.active {
  background: var(--primary);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.filter-count {
  margin-left: 2px;
  opacity: 0.9;
}

/* Masonry Grid */
.bangumi-masonry {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (min-width: 640px) {
  .bangumi-masonry {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

/* Card */
.bangumi-item-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  display: block;
  text-decoration: none;
  transition: transform 0.3s, box-shadow 0.3s;
}

.bangumi-item-card:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.dark .bangumi-item-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

.card-cover-wrap {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
}

.card-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
  transition: transform 0.5s;
}

.bangumi-item-card:hover .card-cover {
  transform: scale(1.05);
}

.card-cover-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(148, 163, 184, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  font-size: 2rem;
  opacity: 0.5;
}

.status-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 500;
  color: #ffffff;
  z-index: 2;
}

.score-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 500;
  color: #ffffff;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  gap: 2px;
  z-index: 2;
}

.score-star {
  font-size: 0.6rem;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, rgba(0, 0, 0, 0.2) 50%, transparent 100%);
  pointer-events: none;
  z-index: 1;
}

.card-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px;
  z-index: 2;
}

.card-title {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.card-year {
  margin: 4px 0 0;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
}

.card-comment {
  margin: 4px 0 0;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.card-tag {
  font-size: 0.6rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
}

.card-tag.tag-more {
  color: rgba(255, 255, 255, 0.6);
}

/* Empty & Loading */
.bangumi-empty-wrap {
  padding: 14px 0 4px;
}

.bangumi-empty-text {
  color: var(--text-secondary);
}

.bangumi-loading {
  margin-top: 8px;
}

/* Pagination */
.pagination-root {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.pagination-inner {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.5rem;
  overflow: hidden;
  color: var(--primary);
  background: var(--card-bg);
  border: none;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.nav-btn:hover:not(.disabled) {
  background: var(--btn-card-bg-hover);
}

.nav-btn:active:not(.disabled) {
  background: var(--btn-card-bg-active);
}

.nav-btn.disabled {
  pointer-events: none;
  color: rgba(0, 0, 0, 0.1);
}

.dark .nav-btn.disabled {
  color: rgba(255, 255, 255, 0.1);
}

.nav-icon {
  font-size: 1.75rem;
}

.page-numbers {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  background: var(--card-bg);
  overflow: hidden;
  color: var(--text-primary);
  font-weight: 700;
}

.dark .page-numbers {
  color: #cbd5e1;
}

.active-slider {
  position: absolute;
  left: 0;
  top: 0;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.5rem;
  background: var(--primary);
  transition: transform 200ms ease;
  z-index: 0;
}

.page-item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  font-weight: 700;
  font-size: 1rem;
}

.page-current {
  color: #ffffff;
}

.dark .page-current {
  color: rgba(0, 0, 0, 0.7);
}

.page-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  transition: color 150ms ease;
}

.page-btn:hover {
  color: var(--primary);
}

.page-btn:active {
  transform: scale(0.9);
}

.ellipsis {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  font-size: 1.25rem;
  color: var(--text-secondary);
}

@media (max-width: 576px) {
  .bangumi-card {
    padding: 16px;
  }

  .bangumi-masonry {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .card-title {
    font-size: 0.75rem;
  }

  .card-info {
    padding: 8px;
  }
}
</style>
