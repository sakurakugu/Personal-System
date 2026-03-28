<script setup lang="ts">
import { ArrowDown, BellFilled, Calendar, Close, CollectionTag, Grid, Guide, HomeFilled, Link, MessageBox, View } from '@element-plus/icons-vue'
import { siBilibili, siGithub } from 'simple-icons'
import { ElCard, ElEmpty, ElIcon, ElPagination, ElSkeleton, ElSpace, ElTag, ElText } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCategories, fetchTags } from '../../features/articles/api'
import type { ArticleQuery, CategoryRecord, TagRecord } from '../../features/articles/types'
import { useAnnouncementCenter } from '../../features/system/announcement-center'
import { trackPageView } from '../../features/system/api'
import { useArticleStore } from '../../stores/article'

const articleStore = useArticleStore()
const router = useRouter()
const {
  visibleAnnouncements,
  loading: announcementLoading,
  ensureAnnouncementsLoaded,
  toggleAnnouncement,
  isExpanded,
  closeAnnouncement,
} = useAnnouncementCenter()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<CategoryRecord[]>([])
const popularTags = ref<TagRecord[]>([])

const homeAnnouncements = computed(() => visibleAnnouncements.value.slice(0, 3))

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

const recentArticles = computed(() => {
  return [...articleStore.articles]
    .sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime())
    .slice(0, 5)
})

function buildBlogRouteQuery() {
  const query: Record<string, string> = {}
  if (search.value) query.search = search.value
  if (categoryFilter.value) query.category = categoryFilter.value
  return Object.keys(query).length ? query : undefined
}

function buildArticleQuery(): ArticleQuery {
  return {
    search: search.value || undefined,
    category: categoryFilter.value || undefined,
  }
}

function syncBlogRoute() {
  void router.replace({
    path: '/blog',
    query: buildBlogRouteQuery(),
  })
}

async function loadHomeData() {
  await Promise.allSettled([
    articleStore.fetchArticles(1, buildArticleQuery()),
    fetchCategoriesSafely(),
    fetchPopularTags(),
    ensureAnnouncementsLoaded(),
  ])
}

onMounted(async () => {
  const query = router.currentRoute.value.query
  search.value = (query.search as string) || ''
  categoryFilter.value = (query.category as string) || null

  await loadHomeData()
  void trackPageView({ path: '/blog' })
})

function goArticle(slug: string) {
  router.push(`/blog/${slug}`)
}

function handlePageChange(page: number) {
  void articleStore.fetchArticles(page, buildArticleQuery())
}

function doSearch() {
  syncBlogRoute()
  void articleStore.fetchArticles(1, buildArticleQuery())
}

function handleCategorySelect(slug: string) {
  categoryFilter.value = slug
  doSearch()
}
</script>

<template>
  <div class="blog-home">
    <!-- 左侧栏 -->
    <aside class="sidebar-left">
      <ElCard class="sidebar-card">
        <div class="profile-section">
          <div class="avatar">
            <img src="https://free.picui.cn/free/2026/03/17/69b8f1dd8a75e.jpg" alt="头像.jpg" title="头像.jpg">
          </div>
          <h3 class="profile-name">Sakurakugu</h3>
          <p class="profile-desc">测试测试测试</p>
          <div class="profile-stats">
            <div class="stat-item">
              <span class="stat-num">{{ articleStore.total || articleStore.articles.length }}</span>
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
          <router-link to="/links" class="nav-item">
            <ElIcon><Link /></ElIcon>
            <span>友链</span>
          </router-link>
        </div>
      </ElCard>
    </aside>

    <!-- 中间主内容区 -->
    <main class="main-area">
      <section v-if="announcementLoading || homeAnnouncements.length > 0" class="announcements-list">
        <ElSkeleton :loading="announcementLoading" animated :rows="2">
          <ElCard
            v-for="item in homeAnnouncements"
            :key="item.id"
            class="announcement-card"
            shadow="hover"
          >
            <div class="announcement-header" @click="toggleAnnouncement(item.id)">
              <div class="announcement-header-left">
                <ElIcon class="announcement-icon"><BellFilled /></ElIcon>
                <span class="announcement-title">{{ item.title }}</span>
              </div>
              <div class="announcement-header-right">
                <span class="announcement-date">{{ new Date(item.created_at).toLocaleDateString() }}</span>
                <ElIcon class="expand-icon" :class="{ 'is-expanded': isExpanded(item.id) }">
                  <ArrowDown />
                </ElIcon>
              </div>
            </div>
            <div
              v-show="isExpanded(item.id)"
              class="announcement-content-wrapper"
            >
              <div class="announcement-content">
                {{ item.content }}
              </div>
              <div class="announcement-close" @click.stop="closeAnnouncement(item.id)">
                <ElIcon><Close /></ElIcon>
              </div>
            </div>
          </ElCard>
        </ElSkeleton>
      </section>

      <ElSkeleton :loading="articleStore.loading" animated>
        <div v-if="articleStore.articles.length === 0 && !articleStore.loading" class="empty-state">
          <ElEmpty description="暂无文章" />
        </div>

        <div class="article-list">
          <ElCard
            v-for="article in articleStore.articles"
            :key="article.id"
            shadow="hover"
            class="article-card"
            @click="goArticle(article.slug)"
          >
            <div v-if="article.cover_url" class="article-cover">
              <img :src="article.cover_url" :alt="article.title">
            </div>
            <div class="article-body">
              <h2 class="article-title">{{ article.title }}</h2>
              <p class="article-excerpt">{{ article.excerpt || '暂无摘要' }}</p>
              <div class="article-meta">
                <ElSpace size="small">
                  <ElTag v-if="article.category" size="small" type="info">{{ article.category.name }}</ElTag>
                  <ElTag v-for="tag in article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                </ElSpace>
                <ElText type="info" style="font-size: 12px">
                  {{ article.author.nickname || article.author.username }} · {{ new Date(article.published_at || article.created_at).toLocaleDateString() }}
                  ·
                  <ElIcon style="vertical-align: middle"><View /></ElIcon>
                  {{ article.view_count }}
                </ElText>
              </div>
            </div>
          </ElCard>
        </div>
      </ElSkeleton>

      <div v-if="articleStore.pages > 1" class="pagination">
        <ElPagination
          :current-page="articleStore.page"
          :page-count="articleStore.pages"
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
  top: 80px;
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

/* 公告列表 */
.announcements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

/* 公告卡片 */
.announcement-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #fff9e6 0%, #fff5d6 100%);
  border: 1px solid #f0e0b0;
  transition: box-shadow 0.2s;
}

.dark .announcement-card {
  background: linear-gradient(135deg, #3d3020 0%, #2d2515 100%);
  border-color: #5a4a30;
}

.announcement-card:hover {
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.15);
}

.announcement-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.announcement-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.announcement-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.announcement-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.announcement-icon {
  color: #e6a23c;
  font-size: 16px;
  flex-shrink: 0;
}

.announcement-title {
  font-weight: 600;
  font-size: 15px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark .announcement-title {
  color: #fbbf24;
}

.announcement-date {
  color: #999;
  font-size: 12px;
}

.announcement-content-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e6d5b0;
}

.announcement-content {
  flex: 1;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.dark .announcement-content {
  color: #d1d5db;
}

.expand-icon {
  font-size: 14px;
  color: #e6a23c;
  transition: transform 0.3s ease;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
}

.announcement-close {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  cursor: pointer;
  transition: color 0.2s;
  font-size: 14px;
  margin-bottom: 2px;
}

.announcement-close:hover {
  color: #888;
}

.dark .announcement-close:hover {
  color: #d1d5db;
}

.empty-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
}

.article-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
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
}
</style>
