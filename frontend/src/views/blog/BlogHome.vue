<script setup lang="ts">
import { HomeFilled, View } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import {
  NCard,
  NEmpty,
  NInput,
  NPagination,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  NText,
} from 'naive-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useArticleStore } from '../../stores/article'
import api from '../../utils/api'

const articleStore = useArticleStore()
const router = useRouter()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<{ id: string; name: string; slug: string }[]>([])
const popularTags = ref<{ id: string; name: string }[]>([])

// 获取热门标签
async function fetchPopularTags() {
  try {
    const { data } = await api.get('/tags')
    popularTags.value = data.slice(0, 10) // 最多显示10个
  } catch {
    popularTags.value = []
  }
}

// 按标签搜索
function searchByTag(tagName: string) {
  search.value = tagName
  doSearch()
}

// 最近更新的文章（取前5篇）
const recentArticles = computed(() => {
  return [...articleStore.articles]
    .sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime())
    .slice(0, 5)
})

onMounted(async () => {
  await articleStore.fetchArticles()
  try {
    const { data } = await api.get('/categories')
    categories.value = data
  } catch {}
  await fetchPopularTags()
  // Record page view
  try { await api.post('/stats/pageview', { path: '/blog' }) } catch {}
})

function goArticle(slug: string) {
  router.push(`/blog/${slug}`)
}

function handlePageChange(page: number) {
  const query: Record<string, string> = {}
  if (search.value) query.search = search.value
  if (categoryFilter.value) query.category = categoryFilter.value
  articleStore.fetchArticles(page, query)
}

function doSearch() {
  const query: Record<string, string> = {}
  if (search.value) query.search = search.value
  if (categoryFilter.value) query.category = categoryFilter.value
  articleStore.fetchArticles(1, query)
}

const categoryOptions = ref<{ label: string; value: string }[]>([])
watch(categories, (cats) => {
  categoryOptions.value = [
    { label: '全部分类', value: '' },
    ...cats.map(c => ({ label: c.name, value: c.slug })),
  ]
}, { immediate: true })
</script>

<template>
  <div class="blog-home">
    <!-- 左侧栏 -->
    <aside class="sidebar-left">
      <NCard class="sidebar-card" :bordered="false">
        <div class="profile-section">
          <div class="avatar">
            <img src="https://free.picui.cn/free/2026/03/17/69b8f1dd8a75e.jpg" alt="头像.jpg" title="头像.jpg" />
          </div>
          <h3 class="profile-name">Sakurakugu</h3>
          <p class="profile-desc">一个喜欢折腾代码的开发者</p>
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
      </NCard>

      <NCard title="🎮 导航" class="sidebar-card" :bordered="false">
        <div class="nav-links">
          <router-link to="/" class="nav-item">
            <ElIcon><HomeFilled /></ElIcon>
            <span>首页</span>
          </router-link>
          <a href="https://github.com/sakurakugu" target="_blank" class="nav-item">
            <span>GitHub</span>
          </a>
        </div>
      </NCard>
    </aside>

    <!-- 中间主内容区 -->
    <main class="main-area">
      <div class="blog-hero">
        <h1 style="display: inline-flex; align-items: center; gap: 8px">
          <ElIcon><HomeFilled /></ElIcon>
          <span>Sakurakuguの小窝</span>
        </h1>
        <p>个人自用</p>
      </div>

      <div class="filter-bar">
        <NInput
          v-model:value="search"
          placeholder="搜索文章..."
          clearable
          style="max-width: 300px"
          @keyup.enter="doSearch"
        />
        <NSelect
          v-model:value="categoryFilter"
          :options="categoryOptions"
          placeholder="分类筛选"
          clearable
          style="width: 160px"
          @update:value="doSearch"
        />
      </div>

      <NSpin :show="articleStore.loading">
        <div v-if="articleStore.articles.length === 0 && !articleStore.loading" class="empty-state">
          <NEmpty description="暂无文章" />
        </div>

        <div class="article-list">
          <NCard
            v-for="article in articleStore.articles"
            :key="article.id"
            hoverable
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
                <NSpace size="small">
                  <NTag v-if="article.category" size="small" type="info">{{ article.category.name }}</NTag>
                  <NTag v-for="tag in article.tags" :key="tag.id" size="small">{{ tag.name }}</NTag>
                </NSpace>
                <NText depth="3" style="font-size: 12px">
                  {{ article.author.nickname || article.author.username }} · {{ new Date(article.published_at || article.created_at).toLocaleDateString() }}
                  ·
                  <ElIcon style="vertical-align: middle"><View /></ElIcon>
                  {{ article.view_count }}
                </NText>
              </div>
            </div>
          </NCard>
        </div>
      </NSpin>

      <div v-if="articleStore.pages > 1" class="pagination">
        <NPagination
          :page="articleStore.page"
          :page-count="articleStore.pages"
          @update:page="handlePageChange"
        />
      </div>
    </main>

    <!-- 右侧栏 -->
    <aside class="sidebar-right">
      <NCard title="🔥 热门标签" class="sidebar-card" :bordered="false">
        <div class="tag-cloud">
          <NTag
            v-for="tag in popularTags"
            :key="tag.id"
            size="small"
            class="tag-item"
            @click="searchByTag(tag.name)"
          >
            {{ tag.name }}
          </NTag>
          <NEmpty v-if="popularTags.length === 0" description="暂无标签" />
        </div>
      </NCard>

      <NCard title="📊 分类" class="sidebar-card" :bordered="false">
        <div class="category-list">
          <div
            v-for="cat in categories"
            :key="cat.id"
            class="category-item"
            @click="categoryFilter = cat.slug; doSearch()"
          >
            <span class="cat-name">{{ cat.name }}</span>
          </div>
          <NEmpty v-if="categories.length === 0" description="暂无分类" />
        </div>
      </NCard>

      <NCard title="📅 最近更新" class="sidebar-card" :bordered="false">
        <div class="recent-list">
          <div
            v-for="article in recentArticles"
            :key="article.id"
            class="recent-item"
            @click="goArticle(article.slug)"
          >
            <span class="recent-title">{{ article.title }}</span>
            <span class="recent-date">{{ new Date(article.updated_at || article.created_at).toLocaleDateString() }}</span>
          </div>
          <NEmpty v-if="recentArticles.length === 0" description="暂无文章" />
        </div>
      </NCard>

      <NCard title="📬 联系方式" class="sidebar-card" :bordered="false">
        <div class="contact-list">
          <a href="https://github.com/sakurakugu" target="_blank" class="contact-item">
            <span class="contact-icon">🐙</span>
            <div class="contact-info">
              <span class="contact-name">GitHub</span>
              <span class="contact-value">@sakurakugu</span>
            </div>
          </a>
          <a href="https://space.bilibili.com/" target="_blank" class="contact-item">
            <span class="contact-icon" style="color: #fb7299">📺</span>
            <div class="contact-info">
              <span class="contact-name">哔哩哔哩</span>
              <span class="contact-value">待填写</span>
            </div>
          </a>
          <!-- 预留其他联系方式 -->
          <div class="contact-item placeholder">
            <span class="contact-icon">📧</span>
            <div class="contact-info">
              <span class="contact-name">邮箱</span>
              <span class="contact-value">待填写</span>
            </div>
          </div>
        </div>
      </NCard>
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
  padding: 24px 16px;
}

/* 左侧栏 */
.sidebar-left {
  position: sticky;
  top: 80px;
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
  margin-bottom: 16px;
  border-radius: 12px;
}

.sidebar-card :deep(.n-card__header) {
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

.profile-desc {
  font-size: 13px;
  color: #888;
  margin-bottom: 16px;
}

.profile-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
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

.cat-name {
  font-size: 14px;
}

/* 最近更新 */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recent-item {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.recent-item:hover {
  background: #f5f7fa;
}

.recent-title {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recent-date {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 联系方式 */
.contact-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.contact-value {
  font-size: 12px;
  color: #888;
}

/* 主内容区 */
.main-area {
  min-width: 0;
}

.blog-hero {
  text-align: center;
  padding: 20px 0 24px;
}

.blog-hero h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.blog-hero p {
  color: #888;
  font-size: 15px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  justify-content: center;
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

.article-excerpt {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.6;
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
    padding: 16px 12px;
  }

  .blog-hero h1 {
    font-size: 22px;
  }

  .sidebar-left,
  .sidebar-right {
    grid-template-columns: 1fr;
  }
}
</style>
