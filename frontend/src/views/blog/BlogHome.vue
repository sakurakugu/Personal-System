<script setup lang="ts">
import { Grid, Guide, HomeFilled, MessageBox } from '@element-plus/icons-vue'
import { siBilibili, siGithub } from 'simple-icons'
import { ElEmpty, ElIcon, ElPagination, ElSkeleton } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchArticleList, fetchCategories, fetchTags } from '../../features/articles/api'
import type { ArticleQuery, ArticleRecord, CategoryRecord, TagRecord } from '../../features/articles/types'
import { fetchFeedList } from '../../features/feed/api'
import type { FeedItemRecord } from '../../features/feed/types'
import { trackPageView } from '../../features/system/api'
import { useAuthStore } from '../../stores/auth'
import { useBlogAppearanceStore } from '../../stores/blog-appearance'
import HomeAnnouncementList from './components/HomeAnnouncementList.vue'
import ArticleFeedCard from './components/ArticleFeedCard.vue'
import MomentFeedCard from './components/MomentFeedCard.vue'
import { useBannerImages } from '../../composables/useBannerImages'

const auth = useAuthStore()
const appearance = useBlogAppearanceStore()
const route = useRoute()
const router = useRouter()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<CategoryRecord[]>([])
const popularTags = ref<TagRecord[]>([])
const recentArticles = ref<ArticleRecord[]>([])
const currentPage = ref(1)
const totalPages = ref(0)
const articleTotal = ref(0)
const feedItems = ref<FeedItemRecord[]>([])
const feedInitialLoading = ref(true)
const feedRefreshing = ref(false)
const showFeedSkeleton = ref(true)

async function fetchCategoriesSafely() {
  try {
    categories.value = await fetchCategories()
  } catch {
    categories.value = []
  }
}

async function fetchPopularTags() {
  try {
    popularTags.value = (await fetchTags()).slice(0, 10)
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
  return Object.keys(query).length ? query : undefined
}

function buildFeedQuery(): ArticleQuery {
  return {
    search: search.value || undefined,
    category: categoryFilter.value || undefined,
  }
}

async function loadRecentArticles() {
  try {
    const data = await fetchArticleList(1)
    recentArticles.value = data.items.slice(0, 5)
    articleTotal.value = data.total
  } catch {
    recentArticles.value = []
    articleTotal.value = 0
  }
}

async function loadFeed(page = 1, options: { silent?: boolean } = {}) {
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

function syncBlogRoute() {
  void router.replace({
    path: '/blog',
    query: buildBlogRouteQuery(),
  })
}

async function loadHomeData() {
  const tasks = [
    loadFeed(1),
    fetchCategoriesSafely(),
    fetchPopularTags(),
    loadRecentArticles(),
  ]

  await Promise.allSettled(tasks)
}

watch(
  () => auth.isAuthenticated,
  (是否已登录, 之前是否已登录) => {
    if (是否已登录 === 之前是否已登录) return
    if (search.value || categoryFilter.value) return

    void Promise.allSettled([
      loadFeed(1, { silent: true }),
      loadRecentArticles(),
    ])
  },
)

onMounted(async () => {
  const query = route.query
  search.value = (query.search as string) || ''
  categoryFilter.value = (query.category as string) || null

  await loadHomeData()
  void trackPageView({ path: '/blog' })
})

function goArticle(slug: string) {
  void router.push(`/blog/${slug}`)
}

function handlePageChange(page: number) {
  void loadFeed(page, { silent: true })
}

function doSearch() {
  syncBlogRoute()
  void loadFeed(1, { silent: true })
}

function handleCategorySelect(slug: string) {
  categoryFilter.value = slug
  doSearch()
}

/* ==================== Banner 轮播 ==================== */
const { images: bannerImages } = useBannerImages()
const currentBannerIndex = ref(0)
let bannerTimer: number | null = null
const isBannerMode = computed(() => appearance.wallpaperMode === 'banner')
const hasWallpaper = computed(() => appearance.wallpaperMode !== 'none')
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

const currentWallpaperStyle = computed(() => {
  const currentImage = bannerImages.value[currentBannerIndex.value] ?? bannerImages.value[0]
  if (!currentImage) return {}
  return {
    backgroundImage: `url("${currentImage}")`,
  }
})

function stopBannerCarousel() {
  if (bannerTimer !== null) {
    window.clearInterval(bannerTimer)
    bannerTimer = null
  }
}

function startBannerCarousel() {
  stopBannerCarousel()
  if (!appearance.bannerCarouselEnabled || !hasWallpaper.value || bannerImages.value.length <= 1) return

  bannerTimer = window.setInterval(() => {
    if (bannerImages.value.length === 0) return
    currentBannerIndex.value = (currentBannerIndex.value + 1) % bannerImages.value.length
  }, 6000)
}

onMounted(() => {
  startBannerCarousel()
})

watch(
  [bannerImages, () => appearance.bannerCarouselEnabled, () => appearance.wallpaperMode],
  () => {
    if (currentBannerIndex.value >= bannerImages.value.length) {
      currentBannerIndex.value = 0
    }
    startBannerCarousel()
  },
)

onUnmounted(() => {
  stopBannerCarousel()
})

/* ==================== Typewriter 打字机效果 (Firefly 风格) ==================== */
const typewriterTexts = ref([
  '欢迎来到我的小窝',
  '记录生活，分享技术',
  '愿每一天都充满阳光',
])
const typewriterDisplay = ref('')
let typewriterInstance: TypewriterEffect | null = null

class TypewriterEffect {
  private texts: string[]
  private currentTextIndex: number = 0
  private currentIndex: number = 0
  private isDeleting: boolean = false
  private timeoutId: number | null = null
  private speed: number
  private deleteSpeed: number
  private pauseTime: number

  constructor(texts: string[], displayRef: { value: string }, speed = 100, deleteSpeed = 50, pauseTime = 2000) {
    this.texts = texts
    this.speed = speed
    this.deleteSpeed = deleteSpeed
    this.pauseTime = pauseTime
    this.displayRef = displayRef
    this.start()
  }

  private displayRef: { value: string }

  private start() {
    if (this.texts.length === 0) return
    this.type()
  }

  private getCurrentText(): string {
    return this.texts[this.currentTextIndex] || ''
  }

  private type() {
    const currentText = this.getCurrentText()
    const segments = this.segmentText(currentText)

    if (this.isDeleting) {
      if (this.currentIndex > 0) {
        this.currentIndex--
        this.displayRef.value = segments.slice(0, this.currentIndex).join('')
        this.timeoutId = window.setTimeout(() => this.type(), this.deleteSpeed)
      } else {
        this.isDeleting = false
        this.currentTextIndex = (this.currentTextIndex + 1) % this.texts.length
        this.timeoutId = window.setTimeout(() => this.type(), this.speed)
      }
    } else {
      if (this.currentIndex < segments.length) {
        this.currentIndex++
        this.displayRef.value = segments.slice(0, this.currentIndex).join('')
        this.timeoutId = window.setTimeout(() => this.type(), this.speed)
      } else {
        if (this.texts.length > 1) {
          this.isDeleting = true
          this.timeoutId = window.setTimeout(() => this.type(), this.pauseTime)
        }
      }
    }
  }

  public destroy() {
    if (this.timeoutId !== null) {
      window.clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
  }

  private segmentText(text: string): string[] {
    const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' })
    return Array.from(segmenter.segment(text), s => s.segment)
  }
}

onMounted(() => {
  typewriterDisplay.value = ''
  typewriterInstance = new TypewriterEffect(typewriterTexts.value, typewriterDisplay, 100, 50, 2000)
})

onUnmounted(() => {
  if (typewriterInstance) {
    typewriterInstance.destroy()
    typewriterInstance = null
  }
})
</script>

<template>
  <div class="blog-home" :class="blogHomeClass" :style="blogHomeStyle">
    <div v-if="hasWallpaper" class="page-wallpaper" aria-hidden="true">
      <div class="page-wallpaper-image" :style="currentWallpaperStyle" />
      <div class="page-wallpaper-mask" />
      <div class="page-wallpaper-glow page-wallpaper-glow-left" />
      <div class="page-wallpaper-glow page-wallpaper-glow-right" />
    </div>

    <!-- Banner -->
    <div v-if="isBannerMode" class="banner">
      <div class="banner-bg">
        <div
          v-for="(src, idx) in bannerImages"
          :key="src"
          class="banner-slide"
          :class="{ active: idx === currentBannerIndex }"
        >
          <img :src="src" :alt="`banner-${idx}`">
        </div>
      </div>
      <div class="top-gradient-highlight" aria-hidden="true" />
      <div class="banner-dim" />
      <div v-if="appearance.bannerTitleEnabled" class="banner-text">
        <h1 class="banner-title">Hello, 你们好呀!</h1>
        <p class="banner-subtitle">
          <span class="typewriter">{{ typewriterDisplay }}</span>
          <span class="typewriter-cursor">|</span>
        </p>
      </div>
      <!-- Waves -->
      <div
        v-if="appearance.bannerWavesEnabled"
        id="header-waves"
        class="waves"
        style="
          position: absolute;
          bottom: -1px;
          width: 100%;
          transform: translateZ(0);
          isolation: isolate;
          contain: layout style;
          margin-bottom: -1px;
          will-change: transform;
          backface-visibility: hidden;
        "
      >
        <svg
          class="waves"
          xmlns="http://www.w3.org/2000/svg"
          xmlns:xlink="http://www.w3.org/1999/xlink"
          viewBox="0 24 150 28"
          preserveAspectRatio="none"
          shape-rendering="geometricPrecision"
          style="
            overflow: visible;
            z-index: 5;
            transform: translateZ(0);
            will-change: transform;
            contain: layout style;
            width: 100%;
            height: 100%;
            display: block;
            backface-visibility: hidden;
          "
        >
          <defs>
            <path
              id="gentle-wave"
              d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v48h-352z"
            />
          </defs>
          <g class="parallax">
            <use
              xlink:href="#gentle-wave"
              x="48"
              y="0"
              style="opacity: 0.25; fill: var(--page-bg)"
            />
            <use
              xlink:href="#gentle-wave"
              x="48"
              y="3"
              style="opacity: 0.5; fill: var(--page-bg)"
            />
            <use
              xlink:href="#gentle-wave"
              x="48"
              y="5"
              style="opacity: 0.65; fill: var(--page-bg)"
            />
            <use
              xlink:href="#gentle-wave"
              x="48"
              y="7"
              style="opacity: 0.75; fill: var(--page-bg)"
            />
          </g>
        </svg>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-grid" :class="{ 'main-grid--banner': isBannerMode }">
      <!-- 左侧栏 -->
      <aside class="sidebar-left">
        <div class="widget-card profile-card">
          <div class="profile-section">
            <div class="avatar">
              <img src="/头像.avif" alt="头像.avif" title="头像.avif">
            </div>
            <div class="profile-info">
              <h3 class="profile-name">Sakurakugu</h3>
              <p class="profile-desc">个人网站</p>
            </div>
            <div class="profile-stats">
              <div class="stat-item">
                <span class="stat-num">{{ articleTotal }}</span>
                <span class="stat-label">文章</span>
              </div>
              <div class="stat-item">
                <span class="stat-num">{{ categories.length }}</span>
                <span class="stat-label">分类</span>
              </div>
            </div>
          </div>
        </div>

        <div class="widget-card">
          <div class="widget-header">
            <ElIcon><Guide /></ElIcon>
            <span>导航</span>
          </div>
          <div class="nav-links">
            <router-link to="/" class="nav-item">
              <ElIcon><HomeFilled /></ElIcon>
              <span>首页</span>
            </router-link>
          </div>
        </div>
      </aside>

      <!-- 中间主内容区 -->
      <main class="main-area">
        <HomeAnnouncementList />

        <ElSkeleton :loading="showFeedSkeleton" animated>
          <div v-if="feedItems.length === 0 && !showFeedSkeleton" class="empty-state">
            <ElEmpty description="暂无内容" />
          </div>

          <div v-loading="feedRefreshing" class="feed-list">
            <template v-for="item in feedItems" :key="`${item.type}-${item.source_id}`">
              <ArticleFeedCard
                v-if="item.type === 'article' && item.article"
                :article="item.article"
                @click="goArticle"
                @tag-click="searchByTag"
              />
              <MomentFeedCard
                v-else-if="item.moment"
                :moment="item.moment"
              />
            </template>
          </div>
        </ElSkeleton>

        <div v-if="totalPages > 1" class="pagination">
          <ElPagination
            :current-page="currentPage"
            :page-count="totalPages"
            layout="prev, pager, next"
            @update:current-page="handlePageChange"
          />
        </div>
      </main>

      <!-- 右侧栏 -->
      <aside class="sidebar-right">
        <div class="widget-card">
          <div class="widget-header">
            <ElIcon><CollectionTag /></ElIcon>
            <span>标签</span>
          </div>
          <div class="tag-cloud">
            <span
              v-for="tag in popularTags"
              :key="tag.id"
              class="tag-item"
              @click="searchByTag(tag.name)"
            >
              {{ tag.name }}
            </span>
            <div v-if="popularTags.length === 0" class="empty-text">暂无标签</div>
          </div>
        </div>

        <div class="widget-card">
          <div class="widget-header">
            <ElIcon><Grid /></ElIcon>
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
            </div>
            <div v-if="categories.length === 0" class="empty-text">暂无分类</div>
          </div>
        </div>

        <div class="widget-card">
          <div class="widget-header">
            <ElIcon><Calendar /></ElIcon>
            <span>最近更新</span>
          </div>
          <div class="recent-list">
            <div
              v-for="article in recentArticles"
              :key="article.id"
              class="recent-item"
              @click="goArticle(article.slug)"
            >
              <span class="recent-title">{{ article.title }}</span>
            </div>
            <div v-if="recentArticles.length === 0" class="empty-text">暂无文章</div>
          </div>
        </div>

        <div class="widget-card">
          <div class="widget-header">
            <ElIcon><MessageBox /></ElIcon>
            <span>联系方式</span>
          </div>
          <div class="contact-list">
            <a href="https://github.com/sakurakugu" target="_blank" class="contact-item">
              <svg class="contact-icon" viewBox="0 0 24 24" width="20" height="20" v-html="siGithub.svg" />
              <div class="contact-info">
                <span class="contact-name">GitHub</span>
                <span class="contact-value">@sakurakugu</span>
              </div>
            </a>
            <a href="https://space.bilibili.com/22731248" target="_blank" class="contact-item">
              <svg class="contact-icon" viewBox="0 0 24 24" width="20" height="20" fill="#fb7299" v-html="siBilibili.svg" />
              <div class="contact-info">
                <span class="contact-name">哔哩哔哩</span>
                <span class="contact-value">@Sakurakugu</span>
              </div>
            </a>
            <div class="contact-item placeholder">
              <svg class="contact-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
              </svg>
              <div class="contact-info">
                <span class="contact-name">邮箱</span>
                <span class="contact-value">待填写</span>
              </div>
            </div>
          </div>
        </div>
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
  --btn-plain-bg-hover: #f5f7fa;
  --btn-plain-bg-active: #eef2f5;
  --line-divider: rgba(0, 0, 0, 0.08);
  --meta-divider: rgba(0, 0, 0, 0.2);
  --content-meta: rgba(0, 0, 0, 0.6);
  --enter-btn-bg: var(--theme-accent-surface);
  --enter-btn-bg-hover: var(--theme-accent-surface-hover);
  --enter-btn-bg-active: var(--theme-accent-surface-active);

  min-height: 100%;
  position: relative;
  isolation: isolate;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.5), transparent 42%),
    linear-gradient(180deg, oklch(0.96 0.008 var(--hue) / 0.86) 0%, oklch(0.96 0.008 var(--hue) / 0.96) 28%, oklch(0.96 0.008 var(--hue)) 100%);
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
  --btn-plain-bg-hover: #334155;
  --btn-plain-bg-active: #2a3a4d;
  --line-divider: rgba(255, 255, 255, 0.08);
  --meta-divider: rgba(255, 255, 255, 0.2);
  --content-meta: rgba(255, 255, 255, 0.6);
  --enter-btn-bg: #334155;
  --enter-btn-bg-hover: #3d5168;
  --enter-btn-bg-active: #475d75;
}

.page-wallpaper {
  position: fixed;
  inset: 0;
  z-index: -2;
  overflow: hidden;
  pointer-events: none;
}

.page-wallpaper-image,
.page-wallpaper-mask,
.page-wallpaper-glow {
  position: absolute;
  inset: 0;
}

.page-wallpaper-image {
  inset: -4%;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  transform: scale(1.08);
  filter: blur(20px) saturate(1.08);
  opacity: 0.72;
  transition: background-image 1s ease, opacity 0.6s ease;
}

.page-wallpaper-mask {
  background:
    radial-gradient(circle at 20% 18%, rgba(255, 255, 255, 0.42) 0%, transparent 30%),
    radial-gradient(circle at 80% 12%, oklch(0.85 0.03 var(--hue) / 0.22) 0%, transparent 24%),
    linear-gradient(180deg, oklch(0.96 0.008 var(--hue) / 0.18) 0%, oklch(0.96 0.008 var(--hue) / 0.88) 24%, oklch(0.96 0.008 var(--hue) / 0.98) 100%);
}

.page-wallpaper-glow {
  filter: blur(72px);
  opacity: 0.42;
}

.page-wallpaper-glow-left {
  background: radial-gradient(circle, oklch(0.75 0.08 var(--hue) / 0.3) 0%, transparent 62%);
  transform: translate(-18%, -10%);
}

.page-wallpaper-glow-right {
  background: radial-gradient(circle, oklch(0.80 0.06 var(--hue) / 0.22) 0%, transparent 58%);
  transform: translate(30%, -18%);
}

.dark .page-wallpaper-image {
  opacity: 0.5;
  filter: blur(22px) saturate(0.95) brightness(0.52);
}

.dark .page-wallpaper-mask {
  background:
    radial-gradient(circle at 18% 18%, oklch(0.75 0.08 var(--hue) / 0.15) 0%, transparent 26%),
    radial-gradient(circle at 82% 14%, oklch(0.80 0.06 var(--hue) / 0.12) 0%, transparent 20%),
    linear-gradient(180deg, oklch(0.19 0.018 var(--hue) / 0.2) 0%, oklch(0.19 0.018 var(--hue) / 0.8) 28%, oklch(0.19 0.018 var(--hue) / 0.96) 100%);
}

.dark .page-wallpaper-glow-left {
  background: radial-gradient(circle, oklch(0.75 0.08 var(--hue) / 0.2) 0%, transparent 62%);
}

.dark .page-wallpaper-glow-right {
  background: radial-gradient(circle, oklch(0.80 0.06 var(--hue) / 0.14) 0%, transparent 58%);
}

.is-overlay-mode .page-wallpaper-image {
  inset: 0;
  transform: scale(1.04);
  filter: blur(var(--overlay-blur)) saturate(1.05);
  opacity: var(--overlay-opacity);
}

.is-overlay-mode .page-wallpaper-mask {
  background:
    radial-gradient(circle at 20% 18%, rgba(255, 255, 255, 0.2) 0%, transparent 28%),
    linear-gradient(180deg, oklch(0.96 0.008 var(--hue) / 0.2) 0%, oklch(0.96 0.008 var(--hue) / 0.58) 30%, oklch(0.96 0.008 var(--hue) / 0.86) 100%);
}

.dark .blog-home.is-overlay-mode .page-wallpaper-mask {
  background:
    radial-gradient(circle at 18% 18%, oklch(0.75 0.08 var(--hue) / 0.12) 0%, transparent 24%),
    linear-gradient(180deg, oklch(0.19 0.018 var(--hue) / 0.14) 0%, oklch(0.19 0.018 var(--hue) / 0.5) 30%, oklch(0.19 0.018 var(--hue) / 0.82) 100%);
}

/* Banner */
.banner {
  position: relative;
  width: 100%;
  height: 65vh;
  min-height: 420px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 0;
  margin-top: -64px;
  padding-top: 64px;
}

.banner-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.banner-slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 1.5s ease-in-out;
}

.banner-slide.active {
  opacity: 1;
}

.banner-slide img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1);
  transition: transform 6s ease-out;
}

.banner-slide.active img {
  animation: kenBurns 6s ease-out forwards;
}

@keyframes kenBurns {
  0% { transform: scale(1); }
  100% { transform: scale(1.1); }
}

.banner-dim {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.35) 100%);
}

.banner-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  text-align: center;
  color: #fff;
  padding: 1rem;
  user-select: none;
}

.banner-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  text-shadow: 0 4px 24px rgba(0, 0, 0, 0.6);
  animation: banner-fadeInUp 0.6s ease-out both;
}

.banner-subtitle {
  font-size: 1.5rem;
  font-weight: 400;
  opacity: 0.95;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.6);
  animation: banner-fadeInUp 0.6s ease-out 0.2s both;
  height: 2.25rem;
  line-height: 2.25rem;
}

.typewriter {
  display: inline;
}

.typewriter-cursor {
  display: inline;
  animation: blink 1s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes banner-fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Waves */
#header-waves {
  height: 15vh;
  max-height: 150px;
  min-height: 50px;
}

@media (max-width: 1023px) {
  #header-waves {
    height: 10vh;
  }
}

#header-waves .parallax {
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
}

#header-waves .parallax use {
  animation: wave 25s cubic-bezier(0.5, 0.5, 0.45, 0.5) infinite;
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
}

#header-waves .parallax use:nth-child(1) {
  animation-delay: -2s;
  animation-duration: 7s;
}

#header-waves .parallax use:nth-child(2) {
  animation-delay: -3s;
  animation-duration: 10s;
}

#header-waves .parallax use:nth-child(3) {
  animation-delay: -4s;
  animation-duration: 13s;
}

#header-waves .parallax use:nth-child(4) {
  animation-delay: -5s;
  animation-duration: 20s;
}

@keyframes wave {
  0% {
    transform: translate3d(-90px, 0, 0);
  }
  100% {
    transform: translate3d(85px, 0, 0);
  }
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 88px 16px 24px;
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
  padding: 14px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--line-divider);
}

.empty-text {
  width: 100%;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 8px 0;
}

/* Profile */
.profile-card .profile-section {
  text-align: center;
  padding: 20px 16px 16px;
}

.avatar {
  width: 88px;
  height: 88px;
  margin: 0 auto 12px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.profile-desc {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.profile-stats {
  display: flex;
  justify-content: center;
  gap: 28px;
  padding-top: 14px;
  border-top: 1px dashed var(--line-divider);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* Nav Links */
.nav-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

/* Tag Cloud */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 14px 14px;
}

.tag-item {
  cursor: pointer;
  font-size: 12px;
  padding: 5px 10px;
  border-radius: 6px;
  background: var(--btn-regular-bg);
  color: var(--text-secondary);
  transition: all 0.2s;
}

.tag-item:hover {
  background: var(--btn-regular-bg-hover);
  color: var(--primary);
  transform: scale(1.03);
}

/* Category List */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px 10px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
  font-size: 14px;
}

.category-item:hover {
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

/* Recent List */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px 10px;
}

.recent-item {
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary);
  font-size: 13px;
}

.recent-item:hover {
  background: var(--btn-plain-bg-hover);
  color: var(--primary);
}

.recent-title {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Contact List */
.contact-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px 10px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}

.contact-item:hover {
  background: var(--btn-plain-bg-hover);
}

.contact-item.placeholder {
  cursor: default;
}

.contact-item.placeholder:hover {
  background: transparent;
}

.contact-icon {
  font-size: 20px;
  width: 28px;
  text-align: center;
  flex-shrink: 0;
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

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0 8px;
}

.top-gradient-highlight {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 180px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0.3) 30%, rgba(255, 255, 255, 0.15) 60%, rgba(255, 255, 255, 0.05) 80%, transparent 100%);
  pointer-events: none;
  z-index: 2;
}

.dark .top-gradient-highlight {
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.3) 30%, rgba(0, 0, 0, 0.15) 60%, rgba(0, 0, 0, 0.05) 80%, transparent 100%);
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
  .page-wallpaper-image {
    inset: -8%;
    transform: scale(1.12);
  }

  .banner {
    height: 70vh;
    min-height: 450px;
  }

  .banner-title {
    font-size: 2.4rem;
  }

  .banner-subtitle {
    font-size: 1.1rem;
  }

  .main-grid {
    padding: 0 12px 20px;
    padding-top: 76px;
  }

  .main-grid--banner {
    padding-top: 0;
    margin-top: -1.5rem;
  }

  .sidebar-left,
  .sidebar-right {
    grid-template-columns: 1fr;
  }

  .profile-card .profile-section {
    display: flex;
    align-items: center;
    gap: 14px;
    text-align: left;
    padding: 16px;
  }

  .avatar {
    width: 68px;
    height: 68px;
    margin: 0;
    flex-shrink: 0;
  }

  .profile-info {
    flex: 1;
    min-width: 0;
  }

  .profile-desc {
    margin-bottom: 0;
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

  .nav-links {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 8px;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .nav-links::-webkit-scrollbar {
    display: none;
  }

  .nav-item {
    flex: 0 0 auto;
    white-space: nowrap;
  }

  :deep(.moment-card) {
    padding: 14px;
  }

  :deep(.moment-header) {
    flex-direction: column;
  }
}

/* 移动端 Banner 高度优化 - Firefly 风格 */
@media (max-width: 480px) {
  .banner {
    height: 70vh !important;
    min-height: 450px;
  }
}

@media (min-width: 481px) and (max-width: 640px) {
  .banner {
    height: 75vh !important;
    min-height: 500px;
  }
}

@media (min-width: 641px) and (max-width: 767px) {
  .banner {
    height: 72vh !important;
    min-height: 520px;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .banner {
    height: 70vh !important;
    min-height: 500px;
  }
}

/* 横屏模式优化 */
@media (max-width: 1023px) and (orientation: landscape) {
  .banner {
    height: 60vh !important;
    min-height: 300px;
  }
}

/* 基于屏幕高度的 Banner 优化 */
@media (max-height: 500px) {
  .banner {
    height: 85vh !important;
    min-height: 350px;
  }
}

@media (min-height: 501px) and (max-height: 600px) {
  .banner {
    height: 80vh !important;
    min-height: 400px;
  }
}

@media (min-height: 601px) and (max-height: 700px) {
  .banner {
    height: 75vh !important;
    min-height: 450px;
  }
}
</style>
