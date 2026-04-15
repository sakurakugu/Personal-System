<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchCategories, fetchTags } from '../../features/articles/api'
import type { CategoryRecord, TagRecord } from '../../features/articles/types'
import { trackPageView } from '../../features/system/api'
import { useAuthStore } from '../../stores/auth'
import { useBlogAppearanceStore } from '../../stores/blog-appearance'
import BlogFeed from './components/BlogFeed.vue'
import SiteStatsWidget from './components/SiteStatsWidget.vue'
import CalendarWidget from './components/CalendarWidget.vue'
import ProfileCard from './components/ProfileCard.vue'
import NavCard from './components/NavCard.vue'
import CategoryBar from './components/CategoryBar.vue'
import ArticleReader from './components/ArticleReader.vue'
import AnnouncementFeed from './components/AnnouncementFeed.vue'
import FriendLinksWidget from './components/FriendLinksWidget.vue'
import ArchiveView from './components/ArchiveView.vue'
import BlogBanner from './components/BlogBanner.vue'

const auth = useAuthStore()
const appearance = useBlogAppearanceStore()
const route = useRoute()
const router = useRouter()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<CategoryRecord[]>([])
const popularTags = ref<TagRecord[]>([])
const totalArticles = ref(0)
const tagsExpanded = ref(false)
const showAnnouncements = ref(true)
const showFilterBar = ref(false)
const previousAnnouncementsState = ref(true)
const activeSort = ref<'comprehensive' | 'latest' | 'hot'>('comprehensive')
const hasSearchFilters = computed(() => Boolean(search.value || categoryFilter.value || activeSort.value !== 'comprehensive'))

/* ==================== 文章阅读 ==================== */
const articleSlug = computed(() => {
  const slug = route.params.slug
  return typeof slug === 'string' ? slug : ''
})

const articleToc = ref<Array<{ id: string; text: string; level: number }>>([])

function backToFeed() {
  articleToc.value = []
  void router.replace('/blog')
}

function scrollToSection(id: string) {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

/* ==================== 视图切换 ==================== */
const viewMode = ref<'feed' | 'archive' | 'announcements' | 'friends'>('feed')

function switchToArchive() {
  viewMode.value = 'archive'
  syncBlogRoute()
}

function switchToAnnouncements() {
  viewMode.value = 'announcements'
  syncBlogRoute()
}

async function fetchCategoriesSafely() {
  try {
    categories.value = await fetchCategories()
  } catch {
    categories.value = []
  }
}

async function fetchPopularTags() {
  try {
    popularTags.value = await fetchTags()
  } catch {
    popularTags.value = []
  }
}

function searchByTag(tagName: string) {
  search.value = tagName
  doSearch()
}

function buildBlogRouteQuery() {
  const query: Record<string, string> = {}
  if (search.value) query.search = search.value
  if (categoryFilter.value) query.category = categoryFilter.value
  if (activeSort.value !== 'comprehensive') query.sort = activeSort.value
  if (viewMode.value === 'archive') query.mode = 'archive'
  else if (viewMode.value === 'announcements') query.mode = 'announcements'
  else if (viewMode.value === 'friends') query.mode = 'friends'
  return Object.keys(query).length ? query : undefined
}

function syncBlogRoute() {
  void router.replace({
    path: '/blog',
    query: buildBlogRouteQuery(),
  })
}

async function loadHomeData() {
  await Promise.allSettled([
    fetchCategoriesSafely(),
    fetchPopularTags(),
  ])
}

watch(
  () => auth.isAuthenticated,
  (是否已登录, 之前是否已登录) => {
    if (是否已登录 === 之前是否已登录) return
  },
)

function syncFromQuery(query: typeof route.query) {
  search.value = (query.search as string) || ''
  categoryFilter.value = (query.category as string) || null
  activeSort.value = (query.sort as 'comprehensive' | 'latest' | 'hot') || 'comprehensive'
  const nextMode = query.mode === 'archive' ? 'archive' : query.mode === 'announcements' ? 'announcements' : query.mode === 'friends' ? 'friends' : 'feed'
  if (viewMode.value !== nextMode) {
    viewMode.value = nextMode
  }
  if (!articleSlug.value) {
    void loadHomeData()
  }
}

watch(() => route.query, (query) => {
  syncFromQuery(query)
}, { deep: true })

onMounted(async () => {
  syncFromQuery(route.query)
  void trackPageView({ path: '/blog' })
})

function goArticle(slug: string) {
  void router.push(`/blog/${slug}`)
}

function doSearch() {
  syncBlogRoute()
}

function handleCategorySelect(slug: string | null) {
  categoryFilter.value = slug
  if (viewMode.value === 'archive' || viewMode.value === 'announcements') {
    viewMode.value = 'feed'
  }
  doSearch()
}

function selectSort(key: string) {
  activeSort.value = key as 'comprehensive' | 'latest' | 'hot'
  if (viewMode.value !== 'feed') {
    viewMode.value = 'feed'
  }
  syncBlogRoute()
}

function clearSearchFilters() {
  search.value = ''
  categoryFilter.value = null
  activeSort.value = 'comprehensive'
  syncBlogRoute()
}

function toggleFilterBar() {
  if (!showFilterBar.value) {
    previousAnnouncementsState.value = showAnnouncements.value
    showAnnouncements.value = false
  } else {
    showAnnouncements.value = previousAnnouncementsState.value
  }
  showFilterBar.value = !showFilterBar.value
}

// 标题高亮逻辑已移至 ArticleFeedCard 组件内

const isBannerMode = computed(() => appearance.wallpaperMode === 'banner')
const blogHomeClass = computed(() => ({
  'is-banner-mode': isBannerMode.value,
  'is-overlay-mode': appearance.wallpaperMode === 'overlay',
  'is-plain-mode': appearance.wallpaperMode === 'none',
}))
const blogHomeStyle = computed(() => ({
  '--overlay-opacity': String(appearance.overlayOpacity / 100),
  '--overlay-blur': `${appearance.overlayBlur}px`,
  '--overlay-card-opacity': String(appearance.overlayCardOpacity / 100),
}))
</script>

<template>
  <div class="blog-home" :class="blogHomeClass" :style="blogHomeStyle">
    <BlogBanner />

    <!-- 主内容区 -->
    <div class="main-grid" :class="{ 'main-grid--banner': isBannerMode && !articleSlug }">
      <!-- 左侧栏 -->
      <aside class="sidebar-left">
        <ProfileCard />

        <NavCard />

        <div class="widget-card">
          <div class="widget-header">
            <span>标签</span>
          </div>
          <div class="tag-cloud" :class="{ 'is-collapsed': !tagsExpanded && popularTags.length > 12 }">
            <span
              v-for="tag in popularTags"
              :key="tag.id"
              class="tag-btn"
              @click="searchByTag(tag.name)"
            >
              {{ tag.name }}
            </span>
            <div v-if="popularTags.length === 0" class="empty-text">暂无标签</div>
          </div>
          <div v-if="popularTags.length > 12 && !tagsExpanded" class="tag-expand" @click="tagsExpanded = true">
            <Icon icon="material-symbols:more-horiz" class="tag-expand-icon" />
            <span>更多</span>
          </div>
        </div>

        <div class="widget-card">
          <div class="widget-header">
            <span>分类</span>
          </div>
          <div class="category-list">
            <div
              v-for="cat in categories"
              :key="cat.id"
              class="category-item"
              @click="handleCategorySelect(cat.slug)"
            >
              <span class="cat-name">{{ cat.name }}</span>
              <span class="cat-count">{{ cat.article_count || 0 }}</span>
            </div>
            <div v-if="categories.length === 0" class="empty-text">暂无分类</div>
          </div>
        </div>
      </aside>

      <!-- 中间主内容区 -->
      <main class="main-area">
        <CategoryBar
          :categories="categories"
          :active-category="categoryFilter"
          :total-articles="totalArticles"
          :view-mode="viewMode"
          :show-announcements="showAnnouncements"
          :show-filter-bar="showFilterBar"
          :has-active-filters="hasSearchFilters"
          @select="handleCategorySelect"
          @archive="switchToArchive"
          @toggle-announcements="showAnnouncements = !showAnnouncements"
          @announcement-click="switchToAnnouncements"
          @toggle-filter="toggleFilterBar"
        />
        <template v-if="articleSlug">
          <ArticleReader
            :slug="articleSlug"
            @back="backToFeed"
            @tag-click="searchByTag"
            @update:toc="articleToc = $event"
          />
        </template>
        <template v-else>
          <BlogFeed
            v-if="viewMode === 'feed'"
            :search="search"
            :category="categoryFilter"
            :active-sort="activeSort"
            :show-announcements="showAnnouncements"
            :show-filter-bar="showFilterBar"
            :is-authenticated="auth.isAuthenticated"
            @update:total-articles="totalArticles = $event"
            @tag-click="searchByTag"
            @article-click="goArticle"
            @sort-change="selectSort"
            @clear-filters="clearSearchFilters"
          />

          <template v-else-if="viewMode === 'announcements'">
            <AnnouncementFeed />
          </template>

          <template v-else-if="viewMode === 'archive'">
            <ArchiveView @click="goArticle" />
          </template>

          <template v-else-if="viewMode === 'friends'">
            <FriendLinksWidget />
          </template>
        </template>
      </main>

      <!-- 右侧栏 -->
      <aside class="sidebar-right">
        <template v-if="articleSlug && articleToc.length">
          <div class="widget-card toc-widget">
            <div class="widget-header">
              <span>文章目录</span>
            </div>
            <div class="toc-list">
              <a
                v-for="item in articleToc"
                :key="item.id"
                :href="`#${item.id}`"
                class="toc-item"
                :class="{ 'toc-h2': item.level === 2, 'toc-h3': item.level === 3 }"
                @click.prevent="scrollToSection(item.id)"
              >
                {{ item.text }}
              </a>
            </div>
          </div>
        </template>
        <template v-else>
          <SiteStatsWidget />
          <CalendarWidget />
        </template>
      </aside>
    </div>
  </div>
</template>

<style scoped>
/* Firefly 主题变量 */
.blog-home {
  --radius-large: 1rem;
  --primary: var(--el-color-primary);
  --card-bg: rgba(255, 255, 255, 0.82);
  --card-bg-transparent: rgba(255, 255, 255, 0.68);
  --page-bg: oklch(0.96 0.008 var(--hue));
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-tertiary: #888888;
  --btn-content: oklch(0.55 0.12 var(--hue));
  --btn-regular-bg: var(--theme-accent-surface);
  --btn-regular-bg-hover: var(--theme-accent-surface-hover);
  --btn-regular-bg-active: var(--theme-accent-surface-active);
  --btn-plain-bg-hover: oklch(0.95 0.025 var(--hue));
  --btn-plain-bg-active: oklch(0.98 0.01 var(--hue));
  --line-divider: rgba(0, 0, 0, 0.08);
  --meta-divider: rgba(0, 0, 0, 0.2);
  --content-meta: rgba(0, 0, 0, 0.6);
  --enter-btn-bg: var(--theme-accent-surface);
  --enter-btn-bg-hover: var(--theme-accent-surface-hover);
  --enter-btn-bg-active: var(--theme-accent-surface-active);

  min-height: 100%;
  position: relative;
  isolation: isolate;
  background: var(--page-bg);
}

.dark .blog-home {
  --card-bg: rgba(15, 23, 42, 0.78);
  --card-bg-transparent: rgba(15, 23, 42, 0.62);
  --page-bg: oklch(0.19 0.018 var(--hue));
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-tertiary: #94a3b8;
  --btn-content: oklch(0.75 0.1 var(--hue));
  --btn-regular-bg: #334155;
  --btn-regular-bg-hover: #3d5168;
  --btn-regular-bg-active: #475d75;
  --btn-plain-bg-hover: oklch(0.30 0.035 var(--hue));
  --btn-plain-bg-active: oklch(0.27 0.025 var(--hue));
  --line-divider: rgba(255, 255, 255, 0.08);
  --meta-divider: rgba(255, 255, 255, 0.2);
  --content-meta: rgba(255, 255, 255, 0.6);
  --enter-btn-bg: #334155;
  --enter-btn-bg-hover: #3d5168;
  --enter-btn-bg-active: #475d75;
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 16px 24px;
  position: relative;
  z-index: 10;
  margin-top: 0;
}

.main-grid--banner {
  padding-top: 0;
  margin-top: -3.5rem;
}

/* 侧边栏 */
.sidebar-left,
.sidebar-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 20;
}

/* Widget Card */
.widget-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s, border-color 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
}

.widget-card:hover {
  box-shadow: 0 18px 34px rgba(148, 163, 184, 0.18);
}

.dark .widget-card:hover {
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.35);
}

.dark .widget-card {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
}

.is-overlay-mode .widget-card,
.is-overlay-mode .feed-card,
.is-overlay-mode .empty-state {
  background: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode .widget-card,
.dark .blog-home.is-overlay-mode .feed-card,
.dark .blog-home.is-overlay-mode .empty-state {
  background: rgba(15, 23, 42, var(--overlay-card-opacity));
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  font-weight: 700;
  font-size: 1.125rem;
  color: var(--text-primary);
  position: relative;
  margin-left: 32px;
  margin-top: 16px;
  margin-bottom: 8px;
  border-bottom: none;
}

.widget-header::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 5.5px;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--primary);
}

.empty-text {
  width: 100%;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 8px 0;
}

/* Tag Cloud */
/* Tag Cloud */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 16px 16px;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.tag-cloud.is-collapsed {
  max-height: 7.5rem;
  padding-bottom: 0;
}

.tag-expand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px 16px;
  color: var(--primary);
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.tag-expand:hover {
  opacity: 0.8;
}

.tag-expand-icon {
  width: 1.75rem;
  height: 1.75rem;
}

.tag-btn {
  display: inline-flex;
  align-items: center;
  height: 32px;
  font-size: 14px;
  padding: 0 12px;
  border-radius: 8px;
  background: var(--btn-regular-bg);
  color: var(--btn-content);
  cursor: pointer;
  transition: all 0.15s;
}

.tag-btn:hover {
  background: var(--btn-regular-bg-hover);
}

.tag-btn:active {
  transform: scale(0.95);
  background: var(--btn-regular-bg-active);
}

/* Category List */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 16px 16px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  height: 40px;
  padding-left: 8px;
  padding-right: 8px;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  padding-left: 12px;
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

.category-item:active {
  background: var(--btn-plain-bg-active);
}

.cat-name {
  overflow: hidden;
  text-align: left;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 15px;
}

.cat-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  min-width: 28px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--btn-content);
  background: oklch(0.95 0.025 var(--hue));
  transition: all 0.2s;
}

.dark .cat-count {
  color: var(--deep-text);
  background: var(--primary);
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.contact-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.contact-value {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* Main Area */
.main-area {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.main-area :deep(.announcements-list) {
  margin-bottom: 0;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
}

/* 文章目录小部件 */
.toc-widget .toc-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 16px 16px;
}

.toc-widget .toc-item {
  display: block;
  padding: 6px 10px;
  border-radius: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.toc-widget .toc-item:hover {
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

.toc-widget .toc-h2 {
  font-weight: 500;
}

.toc-widget .toc-h3 {
  padding-left: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 240px 1fr 240px;
    gap: 16px;
  }
}

@media (max-width: 992px) {
  .main-grid {
    grid-template-columns: 1fr;
    max-width: 800px;
  }

  .main-grid--banner {
    margin-top: -2.5rem;
  }

  .sidebar-left,
  .sidebar-right {
    position: static;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
    top: auto;
  }
}

@media (max-width: 576px) {
  .main-grid {
    padding: 0 12px 20px;
    padding-top: 72px;
  }

  .main-grid--banner {
    padding-top: 0;
    margin-top: -1.5rem;
  }

  .sidebar-left,
  .sidebar-right {
    grid-template-columns: 1fr;
  }

  .profile-stats {
    flex-direction: column;
    justify-content: center;
    gap: 8px;
    padding-top: 0;
    padding-left: 16px;
    border-top: 0;
    border-left: 1px dashed var(--line-divider);
  }

  :deep(.moment-card) {
    padding: 14px;
  }

  :deep(.moment-header) {
    flex-direction: column;
  }
}

</style>
