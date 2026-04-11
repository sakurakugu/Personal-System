<script setup lang="ts">
import { Calendar, CollectionTag, Grid, Guide, HomeFilled, MessageBox, View } from '@element-plus/icons-vue'
import { siBilibili, siGithub } from 'simple-icons'
import { ElCard, ElEmpty, ElIcon, ElPagination, ElSkeleton, ElSpace, ElTag, ElText } from 'element-plus'
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchArticleList, fetchCategories, fetchTags } from '../../features/articles/api'
import type { ArticleQuery, ArticleRecord, CategoryRecord, TagRecord } from '../../features/articles/types'
import { fetchFeedList } from '../../features/feed/api'
import type { FeedItemRecord } from '../../features/feed/types'
import { trackPageView } from '../../features/system/api'
import { useAuthStore } from '../../stores/auth'
import { buildAuthorizedArticleAssetUrl } from '../../utils/articleMedia'
import HomeAnnouncementList from './components/HomeAnnouncementList.vue'

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
</script>

<template>
  <div class="blog-home">
    <!-- 左侧栏 -->
    <aside class="sidebar-left">
      <ElCard class="sidebar-card profile-card">
        <div class="profile-section">
          <div class="avatar">
            <img src="https://free.picui.cn/free/2026/03/17/69b8f1dd8a75e.jpg" alt="头像.jpg" title="头像.jpg">
          </div>
          <div class="profile-info">
            <h3 class="profile-name">Sakurakugu</h3>
            <p class="profile-desc">测试测试测试</p>
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
      </ElCard>

      <ElCard class="sidebar-card">
        <template #header>
          <div class="card-header">
            <ElIcon><Guide /></ElIcon>
            <span>导航</span>
          </div>
        </template>
        <div class="nav-links">
          <router-link to="/" class="nav-item">
            <ElIcon><HomeFilled /></ElIcon>
            <span>首页</span>
          </router-link>
          <!-- 暂时先注释掉，之后再恢复，不要删除 -->
          <!-- <router-link to="/friend-links" class="nav-item">
            <ElIcon><Link /></ElIcon>
            <span>友链</span>
          </router-link> -->
        </div>
      </ElCard>
    </aside>

    <!-- 中间主内容区 -->
    <main class="main-area">
      <HomeAnnouncementList />

      <ElSkeleton :loading="showFeedSkeleton" animated>
        <div v-if="feedItems.length === 0 && !showFeedSkeleton" class="empty-state">
          <ElEmpty description="暂无内容" />
        </div>

        <div v-loading="feedRefreshing" class="feed-list">
          <ElCard
            v-for="item in feedItems"
            :key="`${item.type}-${item.source_id}`"
            shadow="hover"
            class="feed-card"
            :class="item.type === 'article' ? 'article-card' : 'moment-card'"
            @click="item.type === 'article' && item.article ? goArticle(item.article.slug) : undefined"
          >
            <template v-if="item.type === 'article' && item.article">
              <div v-if="item.article.cover_url" class="article-cover">
                <img :src="resolveArticleCoverUrl(item.article.cover_url)" :alt="item.article.title" loading="lazy" decoding="async">
              </div>
              <div class="article-body">
                <h2 class="article-title">{{ item.article.title }}</h2>
                <p class="article-excerpt">{{ item.article.excerpt || '暂无摘要' }}</p>
                <div class="article-meta">
                  <ElSpace size="small">
                    <ElTag v-if="item.article.category" size="small" type="info">{{ item.article.category.name }}</ElTag>
                    <ElTag v-for="tag in item.article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                  </ElSpace>
                  <ElText type="info" style="font-size: 12px">
                    {{ item.article.author.nickname || item.article.author.username }} · {{ new Date(item.article.published_at || item.article.created_at).toLocaleDateString() }}
                    ·
                    <ElIcon style="vertical-align: middle"><View /></ElIcon>
                    {{ item.article.view_count }}
                  </ElText>
                </div>
              </div>
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
              <h2 v-if="item.moment.title" class="article-title moment-title">{{ item.moment.title }}</h2>
              <p class="moment-excerpt">{{ 生成动态摘要(item.moment.content) }}</p>
            </template>
          </ElCard>
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
      <ElCard class="sidebar-card">
        <template #header>
          <div class="card-header">
            <ElIcon><CollectionTag /></ElIcon>
            <span>
              标签</span>
          </div>
        </template>
        <div class="tag-cloud">
          <ElTag
            v-for="tag in popularTags"
            :key="tag.id"
            size="small"
            class="tag-item"
            @click="searchByTag(tag.name)"
          >
            {{ tag.name }}
          </ElTag>
          <div v-if="popularTags.length === 0" class="empty-text">暂无标签</div>
        </div>
      </ElCard>

      <ElCard class="sidebar-card">
        <template #header>
          <div class="card-header">
            <ElIcon><Grid /></ElIcon>
            <span>分类</span>
          </div>
        </template>
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
      </ElCard>

      <ElCard class="sidebar-card">
        <template #header>
          <div class="card-header">
            <ElIcon><Calendar /></ElIcon>
            <span>最近更新</span>
          </div>
        </template>
        <div class="tag-cloud">
          <ElTag
            v-for="article in recentArticles"
            :key="article.id"
            size="small"
            class="tag-item"
            @click="goArticle(article.slug)"
          >
            {{ article.title }}
          </ElTag>
          <div v-if="recentArticles.length === 0" class="empty-text">暂无文章</div>
        </div>
      </ElCard>

      <ElCard class="sidebar-card">
        <template #header>
          <div class="card-header">
            <ElIcon><MessageBox /></ElIcon>
            <span>联系方式</span>
          </div>
        </template>
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
          <!-- 预留其他联系方式 -->
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
      </ElCard>
    </aside>
  </div>
</template>

<style scoped>
/* 三栏布局 */
.blog-home {
  display: grid;
  grid-template-columns: 260px 1fr 260px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px;
}

/* 左侧栏 */
.sidebar-left {
  position: sticky;
  top: 52px;
  height: fit-content;
}

/* 右侧栏 */
.sidebar-right {
  position: sticky;
  top: 52px;
  height: fit-content;
}

/* 侧边栏卡片通用样式 */
.sidebar-card {
  margin-bottom: 12px;
  border-radius: 12px;
}

.sidebar-card :deep(.el-card__body) {
  padding: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 空状态文本 */
.empty-text {
  width: 100%;
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 4px 0;
}

.dark .empty-text {
  color: var(--text-tertiary);
}

.sidebar-card :deep(.el-card__header) {
  font-weight: 600;
  font-size: 14px;
  padding-bottom: 12px;
}

/* 个人信息区 */
.profile-section {
  text-align: center;
  padding: 8px 0;
}

.profile-info {
  display: block;
}

.avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto 12px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  color: #333;
}

.dark .profile-name {
  color: var(--text-primary);
}

.profile-desc {
  font-size: 13px;
  color: #888;
  margin-bottom: 16px;
}

.dark .profile-desc {
  color: var(--text-tertiary);
}

.profile-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.dark .profile-stats {
  border-top-color: var(--border-color);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #18a058;
}

.stat-label {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

.dark .stat-label {
  color: var(--text-tertiary);
}

/* 导航链接 */
.nav-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #555;
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f5f7fa;
  color: #18a058;
}

.dark .nav-item {
  color: var(--text-secondary);
}

.dark .nav-item:hover {
  background: var(--bg-hover);
  color: #4ade80;
}

/* 标签云 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.2s;
}

.tag-item:hover {
  transform: scale(1.05);
}

/* 分类列表 */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  background: #f5f7fa;
  color: #18a058;
}

.dark .category-item {
  color: var(--text-secondary);
}

.dark .category-item:hover {
  background: var(--bg-hover);
  color: #4ade80;
}

.cat-name {
  font-size: 14px;
}

/* 联系方式 */
.contact-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
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
  background: #f5f7fa;
}

.dark .contact-item:hover {
  background: var(--bg-hover);
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
}

.contact-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.contact-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.dark .contact-name {
  color: var(--text-primary);
}

.contact-value {
  font-size: 12px;
  color: #888;
}

.dark .contact-value {
  color: var(--text-tertiary);
}

/* 主内容区 */
.main-area {
  min-width: 0;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feed-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
}

.feed-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.article-card {
  cursor: pointer;
}

.article-cover img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 12px;
}

.article-title {
  font-size: 20px;
  margin-bottom: 8px;
  line-height: 1.4;
}

.dark .article-title {
  color: var(--text-primary);
}

.article-excerpt {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.6;
}

.dark .article-excerpt {
  color: var(--text-secondary);
}

.article-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.moment-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 251, 0.96)),
    linear-gradient(120deg, rgba(24, 160, 88, 0.08), transparent 48%);
  border: 1px solid rgba(24, 160, 88, 0.08);
}

.dark .moment-card {
  background:
    linear-gradient(180deg, rgba(20, 24, 30, 0.96), rgba(28, 34, 42, 0.96)),
    linear-gradient(120deg, rgba(74, 222, 128, 0.12), transparent 48%);
  border-color: rgba(74, 222, 128, 0.14);
}

.moment-card :deep(.el-card__body) {
  padding: 18px 20px;
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
  background: linear-gradient(135deg, #18a058, #34d399);
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
  color: #111827;
  font-size: 14px;
}

.dark .moment-author-meta strong {
  color: var(--text-primary);
}

.moment-title {
  margin-bottom: 10px;
}

.moment-excerpt {
  margin: 0;
  color: #4b5563;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.dark .moment-excerpt {
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .blog-home {
    grid-template-columns: 220px 1fr 220px;
    gap: 16px;
  }
}

@media (max-width: 992px) {
  .blog-home {
    grid-template-columns: 1fr;
    max-width: 800px;
  }

  .sidebar-left,
  .sidebar-right {
    position: static;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }

  .sidebar-card {
    margin-bottom: 0;
  }
}

@media (max-width: 576px) {
  .blog-home {
    padding: 12px;
  }

  .sidebar-left,
  .sidebar-right {
    grid-template-columns: 1fr;
  }

  .profile-card :deep(.el-card__body) {
    padding-left: 18px;
    padding-right: 18px;
  }

  .nav-links {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 10px;
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

  .profile-section {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 0;
    text-align: left;
  }

  .profile-info {
    flex: 1;
    min-width: 0;
  }

  .avatar {
    width: 72px;
    height: 72px;
    margin: 0;
    flex: 0 0 auto;
  }

  .profile-name {
    font-size: 17px;
    margin-bottom: 6px;
  }

  .profile-desc {
    margin-bottom: 0;
    line-height: 1.5;
  }

  .profile-stats {
    justify-content: flex-end;
    gap: 24px;
    padding-left: 20px;
    padding-top: 0;
    border-top: 0;
    border-left: 1px solid #f0f0f0;
    flex: 0 0 auto;
  }

  .dark .profile-stats {
    border-left-color: var(--border-color);
  }

  .stat-item {
    align-items: center;
  }

  .moment-card :deep(.el-card__body) {
    padding: 14px;
  }

  .moment-header {
    flex-direction: column;
  }
}
</style>
