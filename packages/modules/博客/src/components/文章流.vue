<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { 获取文章列表, type ArticleQuery, type ArticleRecord } from '@personal-system/module-articles'
import { MomentComposeCard } from '@personal-system/module-moments'
import { ElEmpty, ElIcon, ElSkeleton } from 'element-plus'
import type { ComponentPublicInstance } from 'vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { fetchFeedList, type FeedItemRecord } from '../feed'
import { 使用博客外观存储 } from '../store'
import AnnouncementList from './公告轮播.vue'
import MomentFeedCard from './动态卡片.vue'
import ArchivePagination from './归档分页.vue'
import ArticleFeedCard from './文章卡片.vue'

const props = defineProps<{
  search: string
  category: string | null
  activeSort: 'comprehensive' | 'latest' | 'hot'
  showMomentComposer: boolean
  showAnnouncements: boolean
  showFilterBar: boolean
  isAuthenticated: boolean
}>()

const emit = defineEmits<{
  (e: 'update:totalArticles', val: number): void
  (e: 'tagClick', name: string): void
  (e: 'articleClick', slug: string): void
  (e: 'momentClick', id: string): void
  (e: 'sortChange', sort: 'comprehensive' | 'latest' | 'hot'): void
  (e: 'clearFilters'): void
  (e: 'published'): void
}>()

const appearance = 使用博客外观存储()

const currentPage = ref(1)
const totalPages = ref(0)
const totalArticles = ref(0)
const feedItems = ref<FeedItemRecord[]>([])
const feedInitialLoading = ref(true)
const feedRefreshing = ref(false)
const showFeedSkeleton = ref(true)
const searchArticles = ref<ArticleRecord[]>([])
const 动态编写卡片引用 = ref<ComponentPublicInstance<{ 保存草稿: () => Promise<void> }> | null>(null)

const hasSearchFilters = computed(() => Boolean(props.search || props.category || props.activeSort !== 'comprehensive'))
const resultCountText = computed(() => hasSearchFilters.value ? `共 ${totalArticles.value} 个结果` : '')
const shouldShowAnnouncements = computed(() => props.showAnnouncements && !props.showMomentComposer)

const isLayoutSwitching = ref(false)
const displayLayout = ref(appearance.postListLayout)

watch(() => appearance.postListLayout, (newLayout, oldLayout) => {
  if (newLayout === oldLayout) return
  isLayoutSwitching.value = true
  setTimeout(() => {
    displayLayout.value = newLayout
    nextTick(() => {
      isLayoutSwitching.value = false
    })
  }, 200)
})

function buildFeedQuery(): ArticleQuery {
  return {
    search: props.search || undefined,
    category: props.category || undefined,
    sort: props.activeSort !== 'comprehensive' ? props.activeSort : undefined,
  }
}

async function loadFeed(page = 1, options: { silent?: boolean } = {}) {
  if (hasSearchFilters.value) {
    await loadSearchArticles(page, options)
  } else {
    await loadFeedItems(page, options)
  }
}

async function loadSearchArticles(page = 1, options: { silent?: boolean } = {}) {
  const silent = options.silent ?? !feedInitialLoading.value
  if (silent) {
    feedRefreshing.value = true
  } else {
    feedInitialLoading.value = true
  }
  try {
    const data = await 获取文章列表(page, buildFeedQuery())
    searchArticles.value = data.items
    currentPage.value = data.page
    totalPages.value = data.pages
    totalArticles.value = data.total
  } catch {
    searchArticles.value = []
    currentPage.value = page
    totalPages.value = 0
    totalArticles.value = 0
  } finally {
    if (silent) {
      feedRefreshing.value = false
    } else {
      feedInitialLoading.value = false
    }
    showFeedSkeleton.value = feedInitialLoading.value && searchArticles.value.length === 0
  }
}

async function loadFeedItems(page = 1, options: { silent?: boolean } = {}) {
  searchArticles.value = []
  const silent = options.silent ?? !feedInitialLoading.value
  if (silent) {
    feedRefreshing.value = true
  } else {
    feedInitialLoading.value = true
  }
  try {
    const data = await fetchFeedList(page, buildFeedQuery())
    feedItems.value = data.items
    currentPage.value = data.page
    totalPages.value = data.pages
    totalArticles.value = data.total
  } catch {
    feedItems.value = []
    currentPage.value = page
    totalPages.value = 0
  } finally {
    if (silent) {
      feedRefreshing.value = false
    } else {
      feedInitialLoading.value = false
    }
    showFeedSkeleton.value = feedInitialLoading.value && feedItems.value.length === 0
  }
}

function handlePageChange(page: number) {
  void loadFeed(page, { silent: true })
}

async function 自动保存并关闭编写区() {
  if (!props.showMomentComposer) {
    return
  }
  await 动态编写卡片引用.value?.保存草稿()
  emit('published')
}

watch(
  [() => props.search, () => props.category, () => props.activeSort],
  async () => {
    await 自动保存并关闭编写区()
    void loadFeed(1, { silent: true })
  },
)

watch(
  () => props.isAuthenticated,
  async (curr, prev) => {
    if (curr === prev) return
    if (props.search || props.category) return
    await 自动保存并关闭编写区()
    void loadFeed(1, { silent: true })
  },
)

watch(totalArticles, (val) => {
  emit('update:totalArticles', val)
})

onMounted(() => {
  void loadFeed(1)
})

defineExpose({
  保存动态草稿并关闭: 自动保存并关闭编写区,
})
</script>

<template>
  <Transition name="feed-switch" mode="out-in">
    <div :key="hasSearchFilters ? 'search' : 'feed'" class="feed-mode-wrapper">
      <!-- 搜索模式：文章结果列表 -->
      <template v-if="hasSearchFilters">
        <div class="filter-bar">
          <div class="filter-row">
            <div class="filter-tabs">
              <button
                v-for="opt in [
                  { key: 'comprehensive', label: '综合' },
                  { key: 'latest', label: '最新' },
                  { key: 'hot', label: '最热' },
                ]"
                :key="opt.key"
                class="filter-tab"
                :class="{ active: activeSort === opt.key }"
                @click="emit('sortChange', opt.key as 'comprehensive' | 'latest' | 'hot')"
              >
                {{ opt.label }}
              </button>
            </div>
            <div class="filter-actions">
              <button class="clear-filter" @click="emit('clearFilters')">
                <ElIcon class="clear-filter-icon"><Close /></ElIcon>
                <span>清除筛选</span>
              </button>
              <div v-if="resultCountText" class="results-stats">{{ resultCountText }}</div>
            </div>
          </div>
        </div>

        <ElSkeleton :loading="showFeedSkeleton" animated>
          <div v-if="searchArticles.length === 0 && !showFeedSkeleton" class="empty-state">
            <ElEmpty description="没有找到相关文章" />
          </div>

          <div v-else v-loading="feedRefreshing" class="feed-list" :class="{ 'grid-mode': displayLayout === 'grid', 'layout-switching': isLayoutSwitching }">
            <ArticleFeedCard
              v-for="article in searchArticles"
              :key="article.id"
              :article="article"
              :highlight-keyword="search"
              :layout="appearance.postListLayout"
              @click="emit('articleClick', $event)"
              @tag-click="emit('tagClick', $event)"
            />
          </div>
        </ElSkeleton>

        <div v-if="totalPages > 1" class="pagination">
          <ArchivePagination
            :current-page="currentPage"
            :total-pages="totalPages"
            @update:current-page="handlePageChange"
          />
        </div>
      </template>

      <!-- 普通 Feed 模式 -->
      <template v-else>
        <Transition name="moment-compose-reveal" appear>
          <MomentComposeCard
            v-if="props.showMomentComposer && props.isAuthenticated"
            ref="动态编写卡片引用"
            title="编写动态"
            overlay-mode
            class="moment-compose-entry"
            @published="() => { emit('published'); void loadFeed(1, { silent: true }) }"
          />
        </Transition>

        <AnnouncementList v-if="shouldShowAnnouncements" />

        <div v-if="showFilterBar" class="filter-bar">
          <div class="filter-row">
            <div class="filter-tabs">
              <button
                v-for="opt in [
                  { key: 'comprehensive', label: '综合' },
                  { key: 'latest', label: '最新' },
                  { key: 'hot', label: '最热' },
                ]"
                :key="opt.key"
                class="filter-tab"
                :class="{ active: activeSort === opt.key }"
                @click="emit('sortChange', opt.key as 'comprehensive' | 'latest' | 'hot')"
              >
                {{ opt.label }}
              </button>
            </div>
            <div class="filter-actions">
              <div v-if="resultCountText" class="results-stats">{{ resultCountText }}</div>
            </div>
          </div>
        </div>

        <ElSkeleton :loading="showFeedSkeleton" animated>
          <div v-if="feedItems.length === 0 && !showFeedSkeleton" class="empty-state">
            <ElEmpty description="暂无内容" />
          </div>

          <div v-loading="feedRefreshing" class="feed-list" :class="{ 'grid-mode': displayLayout === 'grid', 'layout-switching': isLayoutSwitching }">
            <template v-for="item in feedItems" :key="`${item.type}-${item.source_id}`">
              <ArticleFeedCard
                v-if="item.type === 'article' && item.article"
                :article="item.article"
                :layout="appearance.postListLayout"
                @click="emit('articleClick', $event)"
                @tag-click="emit('tagClick', $event)"
              />
              <MomentFeedCard
                v-else-if="item.moment"
                :moment="item.moment"
                @click="emit('momentClick', $event)"
              />
            </template>
          </div>
        </ElSkeleton>

        <div v-if="totalPages > 1" class="pagination">
          <ArchivePagination
            :current-page="currentPage"
            :total-pages="totalPages"
            @update:current-page="handlePageChange"
          />
        </div>
      </template>
    </div>
  </Transition>
</template>

<style scoped>
.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 12px 28px rgba(148, 163, 184, 0.14);
  transition: background-color 0.2s, border-color 0.2s, box-shadow 0.2s;
}

.dark .empty-state {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.empty-state :deep(.el-empty__description) {
  color: var(--text-secondary);
}

.empty-state :deep(.el-empty__description p) {
  color: inherit;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 筛选栏 */
.filter-bar {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  padding: 12px 16px;
  box-shadow: 0 12px 28px rgba(148, 163, 184, 0.14);
  transition: background-color 0.2s, border-color 0.2s, box-shadow 0.2s;
}

.dark .filter-bar {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tabs {
  display: flex;
  gap: 8px;
}

.filter-tab {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tab:hover {
  color: var(--primary);
  background: var(--btn-plain-bg-hover);
}

.filter-tab.active {
  color: var(--primary);
  font-weight: 500;
  background: var(--btn-regular-bg);
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.clear-filter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
  color: var(--btn-content);
  background: transparent;
  border: 1.5px solid var(--line-divider);
  border-radius: 0.5rem;
  white-space: nowrap;
  cursor: pointer;
  transition: border-color 150ms ease-out, color 150ms ease-out, background-color 150ms ease-out;
}

.clear-filter:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: transparent;
}

.dark .clear-filter:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.clear-filter-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  color: inherit;
}

.results-stats {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0 8px;
}

/* ==================== Grid 布局样式 ==================== */
.feed-mode-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.feed-switch-enter-active,
.feed-switch-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.feed-switch-enter-from,
.feed-switch-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.moment-compose-entry {
  transform-origin: top center;
}

.moment-compose-reveal-enter-active,
.moment-compose-reveal-leave-active {
  transition:
    opacity 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    max-height 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    margin-bottom 0.28s cubic-bezier(0.22, 1, 0.36, 1);
  overflow: hidden;
}

.moment-compose-reveal-enter-from,
.moment-compose-reveal-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.985);
  max-height: 0;
  margin-bottom: 0;
}

.moment-compose-reveal-enter-to,
.moment-compose-reveal-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
  max-height: 960px;
  margin-bottom: 0;
}

.feed-list {
  transition: opacity 0.2s ease-out, transform 0.2s ease-out;
}

.feed-list.layout-switching {
  opacity: 0;
  transform: translateY(10px);
}

.feed-list.grid-mode {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

@media (max-width: 992px) {
  .feed-list.grid-mode {
    grid-template-columns: 1fr;
  }
}
</style>
