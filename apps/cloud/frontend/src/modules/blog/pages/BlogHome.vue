<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import AppFooter from '../../../app/components/AppFooter.vue'
import BlogBanner from '../components/BlogBanner.vue'
import BlogHomeMainContent from '../components/BlogHomeMainContent.vue'
import BlogHomeMobileWidgets from '../components/BlogHomeMobileWidgets.vue'
import BlogHomeSidebarLeft from '../components/BlogHomeSidebarLeft.vue'
import BlogHomeSidebarRight from '../components/BlogHomeSidebarRight.vue'
import { useBlogHomePage } from '../composables/useBlogHomePage'
import { useViewport } from '../../../shared/composables/useViewport'

const FloatingToc = defineAsyncComponent(() => import('../components/FloatingToc.vue'))
const { width, isMobileViewport } = useViewport()
const shouldRenderLeftSidebar = computed(() => width.value >= 768)
const shouldRenderRightSidebar = computed(() => width.value >= 1280)

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
  isDetailView,
  currentViewMode,
  articleToc,
  mainViewKey,
  isAuthenticated,
  isBannerMode,
  blogHomeClass,
  blogHomeStyle,
  backToFeed,
  scrollToSection,
  switchToArchive,
  switchToAnnouncements,
  switchToBangumi,
  searchByTag,
  goArticle,
  goMoment,
  handleCategorySelect,
  selectSort,
  clearSearchFilters,
  toggleFilterBar,
} = useBlogHomePage()
</script>

<template>
  <div class="blog-home" :class="blogHomeClass" :style="blogHomeStyle">
    <BlogBanner :view-mode="currentViewMode" :active-category="categoryFilter" :categories="categories" />

    <!-- 主内容区 -->
    <div
      class="main-panel"
      :class="{
        'main-panel--banner': isBannerMode && !isDetailView,
        'main-panel--no-banner': !isBannerMode || isDetailView,
      }"
    >
      <div class="main-panel-inner">
        <div class="main-grid">
          <BlogHomeSidebarLeft
            v-if="shouldRenderLeftSidebar"
            top-class="sidebar-left-top sidebar-col onload-animation"
            sticky-class="sidebar-left-sticky sidebar-col onload-animation"
            :categories="categories"
            :popular-tags="popularTags"
            @tag-click="searchByTag"
            @category-click="handleCategorySelect"
          />

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
            @bangumi="switchToBangumi"
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

          <BlogHomeSidebarRight
            v-if="shouldRenderRightSidebar"
            root-class="sidebar-right-col sidebar-col onload-animation"
            :article-slug="articleSlug"
            :article-toc="articleToc"
            @item-click="scrollToSection"
          />

          <BlogHomeMobileWidgets
            v-if="isMobileViewport"
            root-class="mobile-bottom-col"
            :categories="categories"
            :popular-tags="popularTags"
            @tag-click="searchByTag"
            @category-click="handleCategorySelect"
          />

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

.blog-home.is-overlay-mode {
  --card-bg: rgba(255, 255, 255, var(--overlay-card-opacity-strong));
  --card-bg-transparent: rgba(255, 255, 255, var(--overlay-card-opacity));
}

.dark .blog-home.is-overlay-mode {
  --card-bg: rgba(15, 23, 42, var(--overlay-card-opacity-strong));
  --card-bg-transparent: rgba(15, 23, 42, var(--overlay-card-opacity));
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
:deep(.sidebar-col),
:deep(.sidebar-left-top),
:deep(.sidebar-right-col) {
  display: none;
  flex-direction: column;
  gap: 16px;
}

:deep(.sidebar-left-sticky) {
  display: none;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 80px;
  height: fit-content;
  align-self: start;
}

/* 主内容列 */
:deep(.main-content-col) {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  grid-column: 1;
}

/* 移动端底部组件 */
:deep(.mobile-bottom-col) {
  display: block;
  grid-column: 1 / -1;
}

/* Footer 列 */
.footer-col {
  grid-column: 1 / -1;
}

/* Firefly 切换动画与入场动画 */
:deep(.transition-main) {
  transition:
    opacity var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94),
    transform var(--transition-fast) cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

:deep(.transition-leaving) {
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

:deep(.onload-animation) {
  opacity: 0;
  animation: fade-in-up var(--transition-fast) ease-out forwards;
}

:deep(.onload-animation:nth-child(1)) { animation-delay: 0ms; }
:deep(.onload-animation:nth-child(2)) { animation-delay: 30ms; }
:deep(.onload-animation:nth-child(3)) { animation-delay: 60ms; }
:deep(.onload-animation:nth-child(4)) { animation-delay: 90ms; }
:deep(.onload-animation:nth-child(5)) { animation-delay: 120ms; }

/* Widget Card 基础样式（兼容旧组件） */
:deep(.widget-card) {
  background: var(--card-bg-transparent);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform var(--transition-base), box-shadow var(--transition-base), background-color var(--transition-base), border-color var(--transition-base);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 30px rgba(148, 163, 184, 0.14);
}

:deep(.widget-card:hover) {
  box-shadow: 0 18px 34px rgba(148, 163, 184, 0.18);
}

.dark .blog-home :deep(.widget-card:hover) {
  box-shadow: 0 18px 34px rgba(2, 6, 23, 0.35);
}

.dark .blog-home :deep(.widget-card) {
  border-color: rgba(148, 163, 184, 0.16);
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.28);
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

  :deep(.sidebar-left-top) {
    display: flex;
    grid-area: left-top;
    align-self: start;
  }

  :deep(.sidebar-left-sticky) {
    display: flex;
    grid-area: left-sticky;
  }

  :deep(.sidebar-right-col) {
    display: none;
  }

  :deep(.main-content-col) {
    grid-area: main;
  }

  :deep(.mobile-bottom-col) {
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

  :deep(.sidebar-left-top) {
    display: flex;
    grid-area: left-top;
    align-self: start;
  }

  :deep(.sidebar-left-sticky) {
    display: flex;
    grid-area: left-sticky;
  }

  :deep(.sidebar-right-col) {
    display: flex;
    grid-area: right;
    align-self: stretch;
  }

  :deep(.main-content-col) {
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
