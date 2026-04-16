<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppFooter from '../../components/AppFooter.vue'
import { fetchCategories, fetchTags } from '../../features/articles/api'
import type { CategoryRecord, TagRecord } from '../../features/articles/types'
import { trackPageView } from '../../features/system/api'
import { useAuthStore } from '../../stores/auth'
import { useBlogAppearanceStore } from '../../stores/blog-appearance'
import AboutView from './components/AboutView.vue'
import AnnouncementFeed from './components/AnnouncementFeed.vue'
import ArchiveView from './components/ArchiveView.vue'
import ArticleReader from './components/ArticleReader.vue'
import BangumiView from './components/BangumiView.vue'
import BlogBanner from './components/BlogBanner.vue'
import BlogFeed from './components/BlogFeed.vue'
import BlogTocWidget from './components/BlogTocWidget.vue'
import CalendarWidget from './components/CalendarWidget.vue'
import CategoryBar from './components/CategoryBar.vue'
import CategoryListWidget from './components/CategoryListWidget.vue'
import FriendLinksWidget from './components/FriendLinksWidget.vue'
import NavCard from './components/NavCard.vue'
import ProfileCard from './components/ProfileCard.vue'
import SiteStatsWidget from './components/SiteStatsWidget.vue'
import SponsorView from './components/SponsorView.vue'
import TagCloudWidget from './components/TagCloudWidget.vue'

// const AboutView = defineAsyncComponent(() => import('./components/AboutView.vue'))
// const ArticleReader = defineAsyncComponent(() => import('./components/ArticleReader.vue'))

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
const viewMode = ref<'feed' | 'archive' | 'announcements' | 'friends' | 'about' | 'sponsor' | 'bangumi'>('feed')

function switchToArchive() {
  viewMode.value = 'archive'
  syncBlogRoute()
}

function switchToAnnouncements() {
  viewMode.value = 'announcements'
  syncBlogRoute()
}

function switchToBangumi() {
  viewMode.value = 'bangumi'
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
  else if (viewMode.value === 'sponsor') query.mode = 'sponsor'
  else if (viewMode.value === 'bangumi') query.mode = 'bangumi'
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
  const nextMode = query.mode === 'archive'
    ? 'archive'
    : query.mode === 'announcements'
      ? 'announcements'
      : query.mode === 'friends'
        ? 'friends'
        : query.mode === 'about'
          ? 'about'
          : query.mode === 'sponsor'
            ? 'sponsor'
            : query.mode === 'bangumi'
              ? 'bangumi'
              : 'feed'
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
  if (viewMode.value === 'archive' || viewMode.value === 'announcements' || viewMode.value === 'about' || viewMode.value === 'sponsor' || viewMode.value === 'bangumi') {
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
    <div
      class="main-panel"
      :class="{
        'main-panel--banner': isBannerMode && !articleSlug,
        'main-panel--no-banner': !isBannerMode || articleSlug,
      }"
    >
      <div class="main-panel-inner">
        <div class="main-grid">
          <!-- 左侧顶部：个人资料 -->
          <div class="sidebar-left-top sidebar-col onload-animation">
            <ProfileCard />
          </div>
          <!-- 左侧 sticky：导航、标签、分类 -->
          <aside class="sidebar-left-sticky sidebar-col onload-animation">
            <NavCard />
            <TagCloudWidget :tags="popularTags" @tag-click="searchByTag" />
            <CategoryListWidget :categories="categories" @category-click="handleCategorySelect" />
          </aside>

          <!-- 主内容区 -->
          <div class="main-content-col transition-main">
            <CategoryBar
              :categories="categories"
              :active-category="categoryFilter"
              :total-articles="totalArticles"
              :view-mode="viewMode"
              :show-announcements="showAnnouncements"
              :show-filter-bar="showFilterBar"
              :has-active-filters="hasSearchFilters"
              class="onload-animation"
              @select="handleCategorySelect"
              @archive="switchToArchive"
              @toggle-announcements="showAnnouncements = !showAnnouncements"
              @announcement-click="switchToAnnouncements"
              @bangumi="switchToBangumi"
              @toggle-filter="toggleFilterBar"
            />
            <main class="main-area">
              <Transition name="main-view" mode="out-in">
                <div :key="articleSlug || viewMode" class="main-view-wrapper transition-leaving">
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

                    <template v-else-if="viewMode === 'sponsor'">
                      <SponsorView />
                    </template>

                    <template v-else-if="viewMode === 'bangumi'">
                      <BangumiView />
                    </template>
                  </template>
                </div>
              </Transition>
            </main>
          </div>

          <!-- 右侧栏：站点统计 + 文章目录 / 日期归档 -->
          <div class="sidebar-right-col sidebar-col onload-animation">
            <SiteStatsWidget v-if="!(articleSlug && articleToc.length)" />
            <div class="sidebar-right-sticky">
              <template v-if="articleSlug && articleToc.length">
                <BlogTocWidget :toc="articleToc" @item-click="scrollToSection" />
              </template>
              <template v-else>
                <CalendarWidget />
              </template>
            </div>
          </div>

          <!-- 移动端底部组件 -->
          <div class="mobile-bottom-col">
            <div class="mobile-bottom-widgets">
              <ProfileCard />
              <TagCloudWidget :tags="popularTags" @tag-click="searchByTag" />
              <CategoryListWidget :categories="categories" @category-click="handleCategorySelect" />
              <SiteStatsWidget />
              <CalendarWidget />
            </div>
          </div>

          <!-- Footer -->
          <div class="footer-col">
            <AppFooter />
          </div>
        </div>
      </div>
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
  --btn-card-bg-hover: oklch(0.98 0.005 var(--hue));
  --btn-card-bg-active: oklch(0.9 0.03 var(--hue));
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
  --btn-card-bg-hover: oklch(0.3 0.03 var(--hue));
  --btn-card-bg-active: oklch(0.35 0.035 var(--hue));
  --line-divider: rgba(255, 255, 255, 0.08);
  --meta-divider: rgba(255, 255, 255, 0.2);
  --content-meta: rgba(255, 255, 255, 0.6);
  --enter-btn-bg: #334155;
  --enter-btn-bg-hover: #3d5168;
  --enter-btn-bg-active: #475d75;
}

/* Main Panel - Firefly 风格 */
.main-panel {
  position: relative;
  width: 100%;
  z-index: 10;
}

.main-panel--banner {
  margin-top: -3.5rem;
}

.main-panel--no-banner {
  padding-top: 1.5rem;
}

.main-panel-inner {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
}

/* Main Grid - Firefly 响应式布局 */
.main-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  width: 100%;
  padding: 16px 0 24px;
}

/* 侧边栏列 - 默认移动端隐藏 */
.sidebar-col,
.sidebar-left-top,
.sidebar-right-col {
  display: none;
  flex-direction: column;
  gap: 16px;
}

.sidebar-left-sticky {
  display: none;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 80px;
  height: fit-content;
  align-self: start;
}

.sidebar-right-sticky {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 80px;
  width: 100%;
  min-width: 0;
  height: fit-content;
  align-self: stretch;
}

/* 主内容列 */
.main-content-col {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  grid-column: 1;
}

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

.main-view-enter-active {
  transition:
    opacity 120ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform 120ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.main-view-leave-active {
  transition:
    opacity 120ms cubic-bezier(0.55, 0.055, 0.675, 0.19),
    transform 120ms cubic-bezier(0.55, 0.055, 0.675, 0.19);
}

.main-view-enter-from {
  opacity: 0;
  transform: translateY(2rem);
}

.main-view-leave-to {
  opacity: 0;
  transform: translateY(-2rem);
}

/* 移动端底部组件 */
.mobile-bottom-col {
  display: block;
  grid-column: 1 / -1;
}

.mobile-bottom-widgets {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Footer 列 */
.footer-col {
  grid-column: 1 / -1;
}

/* Firefly 切换动画与入场动画 */
.transition-main {
  transition:
    opacity 120ms cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform 120ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.transition-leaving {
  transition:
    transform 120ms cubic-bezier(0.55, 0.055, 0.675, 0.19),
    opacity 120ms cubic-bezier(0.55, 0.055, 0.675, 0.19);
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(2rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.onload-animation {
  opacity: 0;
  animation: fade-in-up 120ms ease-out forwards;
}

.onload-animation:nth-child(1) { animation-delay: 0ms; }
.onload-animation:nth-child(2) { animation-delay: 30ms; }
.onload-animation:nth-child(3) { animation-delay: 60ms; }
.onload-animation:nth-child(4) { animation-delay: 90ms; }
.onload-animation:nth-child(5) { animation-delay: 120ms; }

/* 右侧栏 sticky 平滑过渡 */
.sidebar-right-sticky {
  transition:
    opacity 0.35s ease-in-out,
    transform 0.35s ease-in-out;
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

/* 平板端 (768px+) - Firefly 风格：显示左侧栏 */
@media (min-width: 768px) {
  .main-grid {
    grid-template-columns: 17.5rem 1fr;
    grid-template-areas:
      "left-top main"
      "left-sticky main"
      "left-sticky footer";
  }

  .sidebar-left-top {
    display: flex;
    grid-area: left-top;
    align-self: start;
  }

  .sidebar-left-sticky {
    display: flex;
    grid-area: left-sticky;
  }

  .sidebar-right-col {
    display: none;
  }

  .main-content-col {
    grid-area: main;
  }

  .mobile-bottom-col {
    display: none;
  }

  .footer-col {
    grid-area: footer;
  }
}

/* 桌面端 (1280px+) - Firefly 风格：双侧栏 */
@media (min-width: 1280px) {
  .main-grid {
    grid-template-columns: 17.5rem 1fr 17.5rem;
    grid-template-areas:
      "left-top main right"
      "left-sticky main right"
      "left-sticky footer right";
  }

  .sidebar-left-top {
    display: flex;
    grid-area: left-top;
    align-self: start;
  }

  .sidebar-left-sticky {
    display: flex;
    grid-area: left-sticky;
  }

  .sidebar-right-col {
    display: flex;
    grid-area: right;
    align-self: stretch;
  }

  .main-content-col {
    grid-area: main;
  }

  .footer-col {
    grid-area: footer;
  }
}

/* 移动端小屏优化 */
@media (max-width: 480px) {
  .main-panel-inner {
    padding: 0 12px;
  }

  .main-grid {
    padding: 0 0 20px;
    padding-top: 72px;
  }

  .main-panel--banner .main-grid {
    padding-top: 0;
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
