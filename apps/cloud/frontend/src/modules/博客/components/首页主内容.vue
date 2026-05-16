<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import type { CategoryRecord } from '@personal-system/module-articles'
import type { BlogSortMode, BlogViewMode } from '../view'
import BlogFeed from './文章流.vue'
import CategoryBar from './分类栏.vue'

const AnnouncementFeed = defineAsyncComponent(() => import('./公告列表.vue'))
const AboutView = defineAsyncComponent(() => import('./关于页面.vue'))
const ArchiveView = defineAsyncComponent(() => import('./归档视图.vue'))
const ArticleReader = defineAsyncComponent(() => import('./文章阅读器.vue'))
const BangumiView = defineAsyncComponent(() => import('./番组视图.vue'))
const FriendLinksWidget = defineAsyncComponent(() => import('./友链组件.vue'))
const GalleryView = defineAsyncComponent(() => import('./相册视图.vue'))
const GuestbookView = defineAsyncComponent(() => import('./留言板.vue'))
const RssView = defineAsyncComponent(() => import('./RSS视图.vue'))
const SponsorView = defineAsyncComponent(() => import('./赞助页面.vue'))
const MomentReader = defineAsyncComponent(() => import('./动态阅读器.vue'))

interface BlogTocItem {
  id: string
  text: string
  level: number
}

defineProps<{
  rootClass: string
  categories: CategoryRecord[]
  search: string
  categoryFilter: string | null
  totalArticles: number
  showAnnouncements: boolean
  showFilterBar: boolean
  activeSort: BlogSortMode
  hasSearchFilters: boolean
  articleSlug: string
  momentId: string
  currentViewMode: BlogViewMode
  articleToc: BlogTocItem[]
  mainViewKey: string
  isAuthenticated: boolean
}>()

const emit = defineEmits<{
  selectCategory: [slug: string | null]
  toggleAnnouncements: []
  announcementClick: []
  archive: []
  bangumi: []
  toggleFilter: []
  'update:totalArticles': [value: number]
  tagClick: [name: string]
  articleClick: [slug: string]
  momentClick: [id: string]
  sortChange: [value: string]
  clearFilters: []
  back: []
  'update:articleToc': [items: BlogTocItem[]]
}>()
</script>

<template>
  <div :class="rootClass">
    <CategoryBar
      :categories="categories"
      :active-category="categoryFilter"
      :total-articles="totalArticles"
      :view-mode="currentViewMode"
      :show-announcements="showAnnouncements"
      :show-filter-bar="showFilterBar"
      :has-active-filters="hasSearchFilters"
      class="onload-animation"
      @select="emit('selectCategory', $event)"
      @archive="emit('archive')"
      @toggle-announcements="emit('toggleAnnouncements')"
      @announcement-click="emit('announcementClick')"
      @bangumi="emit('bangumi')"
      @toggle-filter="emit('toggleFilter')"
    />
    <main class="main-area">
      <Transition name="main-view" mode="out-in">
        <div :key="mainViewKey" class="main-view-wrapper transition-leaving">
          <template v-if="articleSlug">
            <ArticleReader
              :slug="articleSlug"
              @back="emit('back')"
              @tag-click="emit('tagClick', $event)"
              @update:toc="emit('update:articleToc', $event)"
            />
          </template>
          <template v-else-if="momentId">
            <MomentReader :moment-id="momentId" />
          </template>
          <template v-else>
            <BlogFeed
              v-if="currentViewMode === 'feed'"
              :search="search"
              :category="categoryFilter"
              :active-sort="activeSort"
              :show-announcements="showAnnouncements"
              :show-filter-bar="showFilterBar"
              :is-authenticated="isAuthenticated"
              @update:total-articles="emit('update:totalArticles', $event)"
              @tag-click="emit('tagClick', $event)"
              @article-click="emit('articleClick', $event)"
              @moment-click="emit('momentClick', $event)"
              @sort-change="emit('sortChange', $event)"
              @clear-filters="emit('clearFilters')"
            />

            <template v-else-if="currentViewMode === 'announcements'">
              <AnnouncementFeed />
            </template>

            <template v-else-if="currentViewMode === 'archive'">
              <ArchiveView @click="emit('articleClick', $event)" />
            </template>

            <template v-else-if="currentViewMode === 'friends'">
              <FriendLinksWidget />
            </template>

            <template v-else-if="currentViewMode === 'about'">
              <AboutView />
            </template>

            <template v-else-if="currentViewMode === 'guestbook'">
              <GuestbookView />
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
</template>

<style scoped>
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
</style>
