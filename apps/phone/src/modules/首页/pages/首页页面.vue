<script setup lang="ts">
import { BlogHomeMainContent, 使用博客首页 } from '@personal-system/module-blog/home'
import PhoneHomeFloatingControls from '../components/首页浮动控制.vue'

const {
  categories,
  search,
  categoryFilter,
  totalArticles,
  showAnnouncements,
  showFilterBar,
  activeSort,
  hasSearchFilters,
  articleSlug,
  momentId,
  isDetailView,
  currentViewMode,
  articleToc,
  mainViewKey,
  isAuthenticated,
  blogHomeClass,
  blogHomeStyle,
  backToFeed,
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
  blogBasePath: '/blog',
  momentBasePath: '/moments',
  routeNameByView: {
    feed: 'Home',
    archive: 'PhoneBlogArchive',
    announcements: 'PhoneBlogAnnouncements',
    friends: 'Home',
    about: 'Home',
    guestbook: 'Home',
    sponsor: 'Home',
    media: 'Home',
    gallery: 'Home',
    rss: 'Home',
  },
})
</script>

<template>
  <section class="phone-blog-home" :class="blogHomeClass" :style="blogHomeStyle">
    <div class="main-panel">
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
    </div>
    <PhoneHomeFloatingControls :is-detail-view="isDetailView" :toc="articleToc" />
  </section>
</template>

<style scoped>
.phone-blog-home {
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
  width: 100%;
  padding: 12px 12px 24px;
  position: relative;
  isolation: isolate;
  overflow-x: clip;
  background: var(--page-bg);
}

.dark .phone-blog-home {
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

.phone-blog-home.is-overlay-mode {
  --card-bg: rgba(255, 255, 255, var(--overlay-card-opacity-strong));
  --card-bg-transparent: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .phone-blog-home.is-overlay-mode {
  --card-bg: rgba(15, 23, 42, var(--overlay-card-opacity-strong));
  --card-bg-transparent: rgba(15, 23, 42, var(--overlay-card-opacity));
}

.main-panel {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
}

:deep(.main-content-col) {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

:deep(.transition-main) {
  transition:
    opacity var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@media (min-width: 768px) {
  .phone-blog-home {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
