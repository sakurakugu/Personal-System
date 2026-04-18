<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import AppFooter from '../../components/AppFooter.vue'
import { trackPageView } from '../../modules/system/api'
import {
  buildBlogFeedQuery,
  getBlogRouteName,
  parseBlogFeedQuery,
  resolveBlogViewMode,
  type BlogSortMode,
} from '../../features/blog/view'
import type { BlogViewMode } from '../../features/blog/view'
import { useArticleTaxonomyStore } from '../../modules/articles/taxonomy-store'
import { useBlogAppearanceStore } from '../../stores/blog-appearance'
import { useAuthStore } from '../../stores/auth'
import BlogBanner from './components/BlogBanner.vue'
import BlogFeed from './components/BlogFeed.vue'
import CalendarWidget from './components/CalendarWidget.vue'
import CategoryBar from './components/CategoryBar.vue'
import CategoryListWidget from './components/CategoryListWidget.vue'
import NavCard from './components/NavCard.vue'
import ProfileCard from './components/ProfileCard.vue'
import SiteStatsWidget from './components/SiteStatsWidget.vue'
import TagCloudWidget from './components/TagCloudWidget.vue'
const AboutView = defineAsyncComponent(() => import('./components/AboutView.vue'))
const AnnouncementFeed = defineAsyncComponent(() => import('./components/AnnouncementFeed.vue'))
const ArchiveView = defineAsyncComponent(() => import('./components/ArchiveView.vue'))
const ArticleReader = defineAsyncComponent(() => import('./components/ArticleReader.vue'))
const BangumiView = defineAsyncComponent(() => import('./components/BangumiView.vue'))
const GalleryView = defineAsyncComponent(() => import('./components/GalleryView.vue'))
const BlogTocWidget = defineAsyncComponent(() => import('./components/BlogTocWidget.vue'))
const FloatingToc = defineAsyncComponent(() => import('../../components/FloatingToc.vue'))
const FriendLinksWidget = defineAsyncComponent(() => import('./components/FriendLinksWidget.vue'))
const RssView = defineAsyncComponent(() => import('./components/RssView.vue'))
const SponsorView = defineAsyncComponent(() => import('./components/SponsorView.vue'))

const auth = useAuthStore()
const taxonomyStore = useArticleTaxonomyStore()
const appearance = useBlogAppearanceStore()
const route = useRoute()
const router = useRouter()
const { categories, tags: popularTags } = storeToRefs(taxonomyStore)

const search = ref('')
const categoryFilter = ref<string | null>(null)
const totalArticles = ref(0)
const showAnnouncements = ref(true)
const showFilterBar = ref(false)
const previousAnnouncementsState = ref(true)
const activeSort = ref<BlogSortMode>('comprehensive')
const hasSearchFilters = computed(() => Boolean(search.value || categoryFilter.value || activeSort.value !== 'comprehensive'))

const articleSlug = computed(() => {
  const slug = route.params.slug
  return typeof slug === 'string' ? slug : ''
})
const currentViewMode = computed<BlogViewMode>(() => resolveBlogViewMode(route))

const articleToc = ref<Array<{ id: string; text: string; level: number }>>([])

function backToFeed() {
  articleToc.value = []
  void goToBlogFeed({
    search: search.value,
    category: categoryFilter.value,
    sort: activeSort.value,
  }, true)
}

function scrollToSection(id: string) {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function switchToArchive() {
  void goToBlogView('archive')
}

function switchToAnnouncements() {
  void goToBlogView('announcements')
}

function switchToBangumi() {
  void goToBlogView('bangumi')
}

function searchByTag(tagName: string) {
  void goToBlogFeed({
    search: tagName,
    category: null,
    sort: 'comprehensive',
  })
}

function goToBlogView(view: BlogViewMode) {
  return router.push({
    name: getBlogRouteName(view),
  })
}

function goToBlogFeed(
  nextState: {
    search: string
    category: string | null
    sort: BlogSortMode
  },
  replace = false,
) {
  const target = {
    name: 'BlogHome',
    query: buildBlogFeedQuery(nextState),
  }

  if (replace) {
    return router.replace(target)
  }

  return router.push(target)
}

function syncFromRoute() {
  const nextState = parseBlogFeedQuery(route)
  search.value = nextState.search
  categoryFilter.value = nextState.category
  activeSort.value = nextState.sort
}

watch(
  () => route.query,
  () => {
    syncFromRoute()
  },
  { immediate: true },
)

watch(
  () => route.path,
  (path) => {
    if (!articleSlug.value) {
      void trackPageView({ path })
    }
  },
  { immediate: true },
)

watch(
  articleSlug,
  (slug) => {
    if (!slug) {
      articleToc.value = []
    }
  },
)

watch(
  () => route.name,
  () => {
    if (currentViewMode.value !== 'feed') {
      showFilterBar.value = false
    }
  },
)

function goArticle(slug: string) {
  void router.push(`/blog/${slug}`)
}

function doSearch() {
  void goToBlogFeed({
    search: search.value,
    category: categoryFilter.value,
    sort: activeSort.value,
  })
}

void taxonomyStore.ensureLoaded()

function handleCategorySelect(slug: string | null) {
  categoryFilter.value = slug
  if (slug === null) {
    search.value = ''
    activeSort.value = 'comprehensive'
    showFilterBar.value = false
    showAnnouncements.value = true
  } else {
    showAnnouncements.value = false
  }
  doSearch()
}

function selectSort(key: string) {
  activeSort.value = key as BlogSortMode
  doSearch()
}

function clearSearchFilters() {
  search.value = ''
  categoryFilter.value = null
  activeSort.value = 'comprehensive'
  void goToBlogFeed({
    search: '',
    category: null,
    sort: 'comprehensive',
  })
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
    <BlogBanner :view-mode="currentViewMode" :active-category="categoryFilter" :categories="categories" />

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
              :view-mode="currentViewMode"
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
                <div :key="articleSlug || route.path" class="main-view-wrapper transition-leaving">
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
                      v-if="currentViewMode === 'feed'"
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

                    <template v-else-if="currentViewMode === 'announcements'">
                      <AnnouncementFeed />
                    </template>

                    <template v-else-if="currentViewMode === 'archive'">
                      <ArchiveView @click="goArticle" />
                    </template>

                    <template v-else-if="currentViewMode === 'friends'">
                      <FriendLinksWidget />
                    </template>

                    <template v-else-if="currentViewMode === 'about'">
                      <AboutView />
                    </template>

                    <template v-else-if="currentViewMode === 'sponsor'">
                      <SponsorView />
                    </template>

                    <template v-else-if="currentViewMode === 'bangumi'">
                      <BangumiView />
                    </template>

                    <template v-else-if="currentViewMode === 'gallery'">
                      <GalleryView />
                    </template>

                    <template v-else-if="currentViewMode === 'rss'">
                      <RssView />
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

    <!-- 浮动文章目录 -->
    <FloatingToc v-if="articleSlug && articleToc.length" :toc="articleToc" />
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
  --transition-fast: 120ms;
  --transition-base: 0.2s;
  --transition-slow: 0.36s;

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
  max-width: 1500px;
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
    opacity var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.main-view-leave-active {
  transition:
    opacity var(--transition-fast) cubic-bezier(0.55, 0.055, 0.675, 0.19),
    transform var(--transition-fast) cubic-bezier(0.55, 0.055, 0.675, 0.19);
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
    opacity var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.transition-leaving {
  transition:
    transform var(--transition-fast) cubic-bezier(0.55, 0.055, 0.675, 0.19),
    opacity var(--transition-fast) cubic-bezier(0.55, 0.055, 0.675, 0.19);
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
  animation: fade-in-up var(--transition-fast) ease-out forwards;
}

.onload-animation:nth-child(1) { animation-delay: 0ms; }
.onload-animation:nth-child(2) { animation-delay: 30ms; }
.onload-animation:nth-child(3) { animation-delay: 60ms; }
.onload-animation:nth-child(4) { animation-delay: 90ms; }
.onload-animation:nth-child(5) { animation-delay: 120ms; }

/* 右侧栏 sticky 平滑过渡 */
.sidebar-right-sticky {
  transition:
    opacity var(--transition-slow) ease-in-out,
    transform var(--transition-slow) ease-in-out;
}

/* Widget Card 基础样式（兼容旧组件） */
.widget-card {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
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
