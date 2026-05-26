<script setup lang="ts">
import { BlogHomeMainContent, 使用博客首页 } from '@personal-system/module-blog/home'
import { BlogCategoryListWidget, BlogTagCloudWidget } from '@personal-system/module-blog/widgets'
import { computed, defineAsyncComponent } from 'vue'

const BlogTocWidget = defineAsyncComponent(() => import('@personal-system/module-blog/widgets').then((module) => module.BlogTocWidget))
const SiteStatsWidget = defineAsyncComponent(() => import('@personal-system/module-blog/widgets').then((module) => module.BlogSiteStatsWidget))
const CalendarWidget = defineAsyncComponent(() => import('@personal-system/module-blog/widgets').then((module) => module.BlogCalendarWidget))

const {
  categories,
  popularTags,
  search,
  categoryFilter,
  totalArticles,
  showAnnouncements,
  showFilterBar,
  activeSort,
  hasSearchFilters,
  articleSlug,
  momentId,
  currentViewMode,
  articleToc,
  mainViewKey,
  isAuthenticated,
  blogHomeClass,
  blogHomeStyle,
  backToFeed,
  scrollToSection,
  switchToArchive,
  switchToAnnouncements,
  switchToMedia,
  searchByTag,
  goArticle,
  goMoment,
  handleCategorySelect,
  selectSort,
  clearSearchFilters,
  toggleFilterBar,
} = 使用博客首页({
  blogBasePath: '/home/blog',
  momentBasePath: '/home/moments',
  routeNameByView: {
    feed: 'DesktopHome',
    archive: 'DesktopBlogArchive',
    announcements: 'DesktopBlogAnnouncements',
    friends: 'DesktopHome',
    about: 'DesktopHome',
    guestbook: 'DesktopHome',
    sponsor: 'DesktopHome',
    media: 'DesktopHome',
    gallery: 'DesktopHome',
    rss: 'DesktopHome',
  },
})

const shouldShowToc = computed(() => Boolean(articleSlug.value && articleToc.value.length))
</script>

<template>
  <div class="desktop-blog-home" :class="blogHomeClass" :style="blogHomeStyle">
    <div class="main-panel main-panel--no-banner">
      <div class="main-panel-inner">
        <div class="main-grid">
          <aside class="sidebar-left-col">
            <div class="sidebar-left-sticky">
              <BlogTagCloudWidget :tags="popularTags" @tag-click="searchByTag" />
              <BlogCategoryListWidget :categories="categories" @category-click="handleCategorySelect" />
            </div>
          </aside>

          <BlogHomeMainContent
            root-class="main-content-col transition-main"
            :categories="categories"
            :search="search"
            :category-filter="categoryFilter"
            :total-articles="totalArticles"
            :show-announcements="showAnnouncements"
            :show-filter-bar="showFilterBar"
            :active-sort="activeSort"
            :has-search-filters="hasSearchFilters"
            :article-slug="articleSlug"
            :moment-id="momentId"
            :current-view-mode="currentViewMode"
            :article-toc="articleToc"
            :main-view-key="mainViewKey"
            :is-authenticated="isAuthenticated"
            @select-category="handleCategorySelect"
            @archive="switchToArchive"
            @toggle-announcements="showAnnouncements = !showAnnouncements"
            @announcement-click="switchToAnnouncements"
            @media="switchToMedia"
            @toggle-filter="toggleFilterBar"
            @update:total-articles="totalArticles = $event"
            @tag-click="searchByTag"
            @article-click="goArticle"
            @moment-click="goMoment"
            @sort-change="selectSort"
            @clear-filters="clearSearchFilters"
            @back="backToFeed"
            @update:article-toc="articleToc = $event"
          />

          <aside class="sidebar-right-col">
            <div class="sidebar-right-sticky">
              <BlogTocWidget
                v-if="shouldShowToc"
                :toc="articleToc"
                @item-click="scrollToSection"
              />
              <template v-else>
                <SiteStatsWidget />
                <CalendarWidget />
              </template>
              <div class="sidebar-right-merged-left">
                <BlogTagCloudWidget :tags="popularTags" @tag-click="searchByTag" />
                <BlogCategoryListWidget :categories="categories" @category-click="handleCategorySelect" />
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.desktop-blog-home {
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

.dark .desktop-blog-home {
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

.desktop-blog-home.is-overlay-mode {
  --card-bg: rgba(255, 255, 255, var(--overlay-card-opacity-strong));
  --card-bg-transparent: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .desktop-blog-home.is-overlay-mode {
  --card-bg: rgba(15, 23, 42, var(--overlay-card-opacity-strong));
  --card-bg-transparent: rgba(15, 23, 42, var(--overlay-card-opacity));
}

.main-panel {
  position: relative;
  width: 100%;
}

.main-panel--no-banner {
  padding-top: 0.75rem;
}

.main-panel-inner {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;
  padding: 0 16px;
}

.main-grid {
  display: grid;
  grid-template-columns: 17.5rem minmax(0, 1fr) 17.5rem;
  grid-template-areas: 'left main right';
  gap: 16px;
  width: 100%;
  padding: 8px 0 24px;
}

.sidebar-left-col {
  grid-area: left;
  min-width: 0;
}

.sidebar-left-sticky {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 12px;
}

:deep(.main-content-col) {
  grid-area: main;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-right-col {
  grid-area: right;
  min-width: 0;
}

.sidebar-right-sticky {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 12px;
  width: 100%;
  min-width: 0;
  height: fit-content;
  align-self: stretch;
}

.sidebar-right-merged-left {
  display: none;
  flex-direction: column;
  gap: 16px;
}

:deep(.transition-main) {
  transition:
    opacity var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@media (max-width: 1279px) {
  .main-grid {
    grid-template-columns: minmax(0, 1fr) 17.5rem;
    grid-template-areas: 'main right';
  }

  .sidebar-left-col {
    display: none;
  }

  .sidebar-right-merged-left {
    display: flex;
  }
}

@media (max-width: 1080px) {
  .main-panel-inner {
    padding: 0 12px;
  }

  .main-grid {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: 'main';
    padding: 8px 0 20px;
  }

  .sidebar-right-col {
    display: none;
  }
}

@media (max-width: 767px) {
  .main-panel-inner {
    padding: 0 12px;
  }

  .sidebar-left-col,
  .sidebar-right-col {
    display: none;
  }
}

@media (max-width: 480px) {
  .main-grid {
    padding-top: 64px;
  }
}
</style>
