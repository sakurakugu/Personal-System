<script setup lang="ts">
import { Calendar, CollectionTag, Grid, Guide, HomeFilled, MessageBox, View } from '@element-plus/icons-vue'
import { siBilibili, siGithub } from 'simple-icons'
import { ElEmpty, ElIcon, ElPagination, ElSkeleton, ElSpace, ElTag, ElText } from 'element-plus'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchArticleList, fetchCategories, fetchTags } from '../../features/articles/api'
import type { ArticleQuery, ArticleRecord, CategoryRecord, TagRecord } from '../../features/articles/types'
import { fetchFeedList } from '../../features/feed/api'
import type { FeedItemRecord } from '../../features/feed/types'
import { trackPageView } from '../../features/system/api'
import { useAuthStore } from '../../stores/auth'
import { buildAuthorizedArticleAssetUrl } from '../../utils/articleMedia'
import HomeAnnouncementList from './components/HomeAnnouncementList.vue'
import { useBannerImages } from '../../composables/useBannerImages'

const auth = useAuthStore()
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

function 生成动态摘要(content: string) {
  return content.length > 220 ? `${content.slice(0, 220)}...` : content
}

function 格式化动态时间(date: string | null) {
  if (!date) return '刚刚'
  return new Date(date).toLocaleString('zh-CN')
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

function resolveArticleCoverUrl(url: string | null) {
  return buildAuthorizedArticleAssetUrl(url)
}

/* ==================== Banner 轮播 ==================== */
const { images: bannerImages } = useBannerImages()
const currentBannerIndex = ref(0)
let bannerTimer: number | null = null

function startBannerCarousel() {
  bannerTimer = window.setInterval(() => {
    if (bannerImages.value.length === 0) return
    currentBannerIndex.value = (currentBannerIndex.value + 1) % bannerImages.value.length
  }, 6000)
}

onMounted(() => {
  startBannerCarousel()
})

onUnmounted(() => {
  if (bannerTimer) window.clearInterval(bannerTimer)
})

/* ==================== Typewriter 打字机效果 ==================== */
const typewriterTexts = ref([
  '欢迎来到我的小窝',
  '记录生活，分享技术',
  '愿每一天都充满阳光',
])
const typewriterDisplay = ref('')
const typewriterPhase = ref<'typing' | 'deleting' | 'waiting'>('waiting')
const typewriterIndex = ref(0)
let typewriterTimer: number | null = null

function clearTypewriterTimer() {
  if (typewriterTimer) {
    window.clearTimeout(typewriterTimer)
    typewriterTimer = null
  }
}

function runTypewriter() {
  const fullText = typewriterTexts.value[typewriterIndex.value]
  const current = typewriterDisplay.value

  if (typewriterPhase.value === 'typing') {
    if (current.length < fullText.length) {
      typewriterDisplay.value = fullText.slice(0, current.length + 1)
      typewriterTimer = window.setTimeout(runTypewriter, 120)
    } else {
      typewriterPhase.value = 'waiting'
      typewriterTimer = window.setTimeout(() => {
        typewriterPhase.value = 'deleting'
        runTypewriter()
      }, 2000)
    }
  } else if (typewriterPhase.value === 'deleting') {
    if (current.length > 0) {
      typewriterDisplay.value = current.slice(0, -1)
      typewriterTimer = window.setTimeout(runTypewriter, 60)
    } else {
      typewriterIndex.value = (typewriterIndex.value + 1) % typewriterTexts.value.length
      typewriterPhase.value = 'typing'
      runTypewriter()
    }
  } else {
    typewriterPhase.value = 'typing'
    runTypewriter()
  }
}

onMounted(() => {
  typewriterPhase.value = 'typing'
  runTypewriter()
})

onUnmounted(() => {
  clearTypewriterTimer()
})
</script>

<template>
  <div class="blog-home">
    <!-- Banner -->
    <div class="banner">
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
      <div class="banner-dim" />
      <div class="banner-text">
        <h1 class="banner-title">Sakurakugu</h1>
        <p class="banner-subtitle">
          <span class="typewriter">{{ typewriterDisplay }}</span>
          <span class="typewriter-cursor">|</span>
        </p>
      </div>
      <!-- Waves -->
      <div
        id="header-waves"
        class="waves"
        style="
          position: absolute;
          bottom: -1px;
          height: 10vh;
          max-height: 150px;
          min-height: 50px;
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
    <div class="main-grid">
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
            <!-- 文章卡片 -->
            <div
              v-for="item in feedItems"
              :key="`${item.type}-${item.source_id}`"
              class="feed-card"
              :class="item.type === 'article' ? 'article-card' : 'moment-card'"
            >
              <template v-if="item.type === 'article' && item.article">
                <div class="article-content" @click="goArticle(item.article.slug)">
                  <a class="article-title">
                    {{ item.article.title }}
                  </a>
                  <div class="article-meta">
                    <ElSpace size="small">
                      <ElTag v-if="item.article.category" size="small" type="info">{{ item.article.category.name }}</ElTag>
                      <ElTag v-for="tag in item.article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                    </ElSpace>
                  </div>
                  <p class="article-excerpt">{{ item.article.excerpt || '暂无摘要' }}</p>
                  <div class="article-footer">
                    <ElText type="info" style="font-size: 12px">
                      {{ item.article.author.nickname || item.article.author.username }} · {{ new Date(item.article.published_at || item.article.created_at).toLocaleDateString() }}
                      ·
                      <ElIcon style="vertical-align: middle"><View /></ElIcon>
                      {{ item.article.view_count }}
                    </ElText>
                  </div>
                </div>
                <div v-if="item.article.cover_url" class="article-cover">
                  <img :src="resolveArticleCoverUrl(item.article.cover_url)" :alt="item.article.title" loading="lazy" decoding="async">
                </div>
                <a v-else class="article-enter" @click="goArticle(item.article.slug)">
                  <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z" />
                  </svg>
                </a>
              </template>

              <template v-else-if="item.moment">
                <div class="moment-header">
                  <div class="moment-author">
                    <div class="moment-avatar">
                      <img v-if="item.moment.user?.avatar_url" :src="item.moment.user.avatar_url" :alt="item.moment.user.nickname || item.moment.user.username">
                      <span v-else>{{ (item.moment.user?.nickname || item.moment.user?.username || '我').slice(0, 1) }}</span>
                    </div>
                    <div class="moment-author-meta">
                      <strong>{{ item.moment.user?.nickname || item.moment.user?.username || '未知用户' }}</strong>
                      <ElText type="info">{{ 格式化动态时间(item.moment.published_at) }}</ElText>
                    </div>
                  </div>
                  <ElTag size="small" type="success" effect="plain">动态</ElTag>
                </div>
                <h2 v-if="item.moment.title" class="moment-title">{{ item.moment.title }}</h2>
                <p class="moment-excerpt">{{ 生成动态摘要(item.moment.content) }}</p>
              </template>
            </div>
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
  --card-bg: #ffffff;
  --card-bg-transparent: rgba(255, 255, 255, 0.72);
  --page-bg: #f5f7fa;
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-tertiary: #888888;
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
  background: var(--page-bg);
}

.dark .blog-home {
  --card-bg: #1e293b;
  --card-bg-transparent: rgba(30, 41, 59, 0.72);
  --page-bg: #0f172a;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-tertiary: #94a3b8;
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

/* Banner */
.banner {
  position: relative;
  width: 100%;
  height: 70vh;
  min-height: 420px;
  max-height: 720px;
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
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.25) 0%, rgba(0, 0, 0, 0.35) 100%);
}

.banner-text {
  position: relative;
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
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
  animation: banner-fadeInUp 0.6s ease-out both;
}

.banner-subtitle {
  font-size: 1.5rem;
  font-weight: 400;
  opacity: 0.95;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.6);
  animation: banner-fadeInUp 0.6s ease-out 0.2s both;
  height: 2.25rem;
  line-height: 2.25rem;
}

.typewriter {
  display: inline;
}

.typewriter-cursor {
  display: inline;
  animation: blink 1s step-end infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
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
  padding: 0 16px 24px;
  position: relative;
  z-index: 10;
  margin-top: -6rem;
}

/* 侧边栏 */
.sidebar-left,
.sidebar-right {
  position: sticky;
  top: 88px;
  height: fit-content;
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-self: start;
  z-index: 20;
}

/* Widget Card */
.widget-card {
  background: var(--card-bg);
  border-radius: var(--radius-large);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
  border: 1px solid var(--line-divider);
}

.widget-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.dark .widget-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
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

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--card-bg);
  border-radius: var(--radius-large);
  border: 1px solid var(--line-divider);
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Feed Card */
.feed-card {
  background: var(--card-bg);
  border-radius: var(--radius-large);
  overflow: hidden;
  border: 1px solid var(--line-divider);
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
}

.feed-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.dark .feed-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

/* Article Card */
.article-card {
  display: flex;
  flex-direction: row-reverse;
  align-items: stretch;
  min-height: 180px;
}

.article-card .article-content {
  flex: 1;
  min-width: 0;
  padding: 22px 20px 20px 24px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.article-title {
  display: block;
  font-size: 1.35rem;
  font-weight: 700;
  margin-bottom: 10px;
  line-height: 1.4;
  color: var(--text-primary);
  text-decoration: none;
  position: relative;
  padding-left: 14px;
  transition: color 0.2s;
}

.article-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  width: 4px;
  height: 20px;
  border-radius: 2px;
  background: var(--primary);
}

.article-title:hover {
  color: var(--primary);
}

.article-meta {
  margin-bottom: 10px;
}

.article-excerpt {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
  display: -webkit-box;
  -line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
  flex: 1;
}

.article-footer {
  margin-top: auto;
}

.article-cover {
  width: 34%;
  min-width: 180px;
  max-width: 320px;
  position: relative;
  overflow: hidden;
}

.article-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.article-card:hover .article-cover img {
  transform: scale(1.06);
}

.article-enter {
  width: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--enter-btn-bg);
  color: var(--primary);
  cursor: pointer;
  transition: background 0.2s;
  text-decoration: none;
}

.article-enter:hover {
  background: var(--enter-btn-bg-hover);
}

/* Moment Card */
.moment-card {
  padding: 18px 20px;
  background:
    linear-gradient(180deg, var(--card-bg) 0%, rgba(240, 247, 243, 0.5) 100%);
}

.dark .moment-card {
  background:
    linear-gradient(180deg, var(--card-bg) 0%, rgba(51, 65, 85, 0.35) 100%);
}

.moment-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.moment-author {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.moment-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 50%;
  background: var(--theme-accent-gradient);
  color: #fff;
  font-weight: 700;
}

.moment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.moment-author-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.moment-author-meta strong {
  color: var(--text-primary);
  font-size: 14px;
}

.moment-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.moment-excerpt {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0 8px;
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
    margin-top: -4rem;
    max-width: 800px;
  }

  .sidebar-left,
  .sidebar-right {
    position: static;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
    top: auto;
  }

  .article-card {
    flex-direction: column-reverse;
    min-height: auto;
  }

  .article-card .article-content {
    padding: 16px;
  }

  .article-cover {
    width: 100%;
    max-width: none;
    min-width: auto;
    height: 180px;
  }

  .article-enter {
    display: none;
  }
}

@media (max-width: 576px) {
  .banner {
    height: 55vh;
    min-height: 320px;
  }

  .banner-title {
    font-size: 2.4rem;
  }

  .banner-subtitle {
    font-size: 1.1rem;
  }

  .main-grid {
    padding: 0 12px 20px;
    margin-top: -3rem;
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

  .article-title {
    font-size: 1.15rem;
  }

  .article-title::before {
    top: 4px;
    height: 16px;
  }

  .moment-card {
    padding: 14px;
  }

  .moment-header {
    flex-direction: column;
  }
}
</style>
