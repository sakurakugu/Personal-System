<script setup lang="ts">
import { computed, defineAsyncComponent, ref, type Component, type ComponentPublicInstance } from 'vue'
import type { CategoryRecord } from '@personal-system/module-articles'
import type { BlogSortMode, BlogViewMode } from '../view'
import BlogFeed from './文章流.vue'
import CategoryBar from './分类栏.vue'

const AnnouncementFeed = defineAsyncComponent(() => import('./公告列表.vue'))
const ArchiveView = defineAsyncComponent(() => import('./归档视图.vue'))
const ArticleReader = defineAsyncComponent(() => import('./文章阅读器.vue'))
const MomentReader = defineAsyncComponent(() => import('./动态阅读器.vue'))

interface BlogTocItem {
  id: string
  text: string
  level: number
}

type BlogExtraViewMode = Exclude<BlogViewMode, 'feed' | 'archive' | 'announcements'>
type BlogExtraViews = Partial<Record<BlogExtraViewMode, Component>>

const props = defineProps<{
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
  extraViews?: BlogExtraViews
}>()

type 博客信息流实例 = ComponentPublicInstance<{
  保存动态草稿并关闭: () => Promise<void>
}>

const emit = defineEmits<{
  selectCategory: [slug: string | null]
  toggleAnnouncements: []
  announcementClick: []
  archive: []
  media: []
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

function 是否为扩展视图模式(mode: BlogViewMode): mode is BlogExtraViewMode {
  return mode !== 'feed' && mode !== 'archive' && mode !== 'announcements'
}

const 显示动态编写区 = ref(false)
const 博客信息流引用 = ref<博客信息流实例 | null>(null)

const 当前扩展视图组件 = computed(() => {
  const mode = props.currentViewMode
  if (!是否为扩展视图模式(mode)) {
    return null
  }
  return props.extraViews?.[mode] ?? null
})

function 打开动态编写弹窗() {
  显示动态编写区.value = !显示动态编写区.value
}

function 收起动态编写区() {
  显示动态编写区.value = false
}

async function 自动保存并收起动态编写区() {
  await 博客信息流引用.value?.保存动态草稿并关闭()
  收起动态编写区()
}
</script>

<template>
  <div :class="rootClass">
    <CategoryBar
      :categories="categories"
      :active-category="categoryFilter"
      :total-articles="totalArticles"
      :view-mode="currentViewMode"
      :is-authenticated="isAuthenticated"
      :show-moment-composer="显示动态编写区"
      :show-announcements="showAnnouncements"
      :show-filter-bar="showFilterBar"
      :has-active-filters="hasSearchFilters"
      class="onload-animation"
      @select="emit('selectCategory', $event)"
      @archive="自动保存并收起动态编写区(); emit('archive')"
      @write-moment="打开动态编写弹窗"
      @toggle-announcements="收起动态编写区(); emit('toggleAnnouncements')"
      @announcement-click="自动保存并收起动态编写区(); emit('announcementClick')"
      @media="自动保存并收起动态编写区(); emit('media')"
      @toggle-filter="收起动态编写区(); emit('toggleFilter')"
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
              ref="博客信息流引用"
              v-if="currentViewMode === 'feed'"
              :search="search"
              :category="categoryFilter"
              :active-sort="activeSort"
              :show-moment-composer="显示动态编写区"
              :show-announcements="showAnnouncements"
              :show-filter-bar="showFilterBar"
              :is-authenticated="isAuthenticated"
              @update:total-articles="emit('update:totalArticles', $event)"
              @tag-click="emit('tagClick', $event)"
              @article-click="emit('articleClick', $event)"
              @moment-click="emit('momentClick', $event)"
              @sort-change="emit('sortChange', $event)"
              @clear-filters="emit('clearFilters')"
              @published="收起动态编写区"
            />

            <template v-else-if="currentViewMode === 'announcements'">
              <AnnouncementFeed />
            </template>

            <template v-else-if="currentViewMode === 'archive'">
              <ArchiveView @click="emit('articleClick', $event)" />
            </template>

            <component :is="当前扩展视图组件" v-else-if="当前扩展视图组件" />
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
