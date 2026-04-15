<script setup lang="ts">
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
import TagCloudWidget from './components/TagCloudWidget.vue'
import CategoryListWidget from './components/CategoryListWidget.vue'
import BlogTocWidget from './components/BlogTocWidget.vue'
import CategoryBar from './components/CategoryBar.vue'
import ArticleReader from './components/ArticleReader.vue'
import AnnouncementFeed from './components/AnnouncementFeed.vue'
import FriendLinksWidget from './components/FriendLinksWidget.vue'
import ArchiveView from './components/ArchiveView.vue'
import AboutView from './components/AboutView.vue'
import BlogBanner from './components/BlogBanner.vue'
import AppFooter from '../../components/AppFooter.vue'

const auth = useAuthStore()
const appearance = useBlogAppearanceStore()
const route = useRoute()
const router = useRouter()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<CategoryRecord[]>([])
const popularTags = ref<TagRecord[]>([])
const totalArticles = ref(0)
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
const viewMode = ref<'feed' | 'archive' | 'announcements' | 'friends' | 'about'>('feed')

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
  else if (viewMode.value === 'about') query.mode = 'about'
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
  const nextMode = query.mode === 'archive' ? 'archive' : query.mode === 'announcements' ? 'announcements' : query.mode === 'friends' ? 'friends' : query.mode === 'about' ? 'about' : 'feed'
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
  if (viewMode.value === 'archive' || viewMode.value === 'announcements' || viewMode.value === 'about') {
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

        <TagCloudWidget :tags="popularTags" @tag-click="searchByTag" />

        <CategoryListWidget :categories="categories" @category-click="handleCategorySelect" />
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
        <Transition name="main-view" mode="out-in">
          <div :key="articleSlug || viewMode" class="main-view-wrapper">
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

              <template v-else-if="viewMode === 'about'">
                <AboutView />
              </template>
            </template>
          </div>
        </Transition>

        <AppFooter />
      </main>

      <!-- 右侧栏 -->
      <aside class="sidebar-right">
        <template v-if="articleSlug && articleToc.length">
          <BlogTocWidget :toc="articleToc" @item-click="scrollToSection" />
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
  transition: margin-top 0.5s ease, padding-top 0.5s ease;
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

/* Widget Card 基础样式（兼容旧组件） */
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
.is-overlay-mode :deep(.feed-card),
.is-overlay-mode :deep(.empty-state) {
  background: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode .widget-card,
.dark .blog-home.is-overlay-mode :deep(.feed-card),
.dark .blog-home.is-overlay-mode :deep(.empty-state) {
  background: rgba(15, 23, 42, var(--overlay-card-opacity));
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

.main-view-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.main-view-enter-active,
.main-view-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.main-view-enter-from,
.main-view-leave-to {
  opacity: 0;
  transform: translateY(8px);
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
