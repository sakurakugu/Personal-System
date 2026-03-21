<script setup lang="ts">
import { ArrowLeft, Search, Close } from '@element-plus/icons-vue'
import { ElButton, ElCard, ElEmpty, ElIcon, ElInput, ElPagination, ElSkeleton, ElSpace, ElTag, ElText } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useArticleStore } from '../../stores/article'
import api from '../../utils/api'

const articleStore = useArticleStore()
const router = useRouter()
const route = useRoute()

// 搜索参数
const searchKeyword = ref('')
const activeSort = ref('comprehensive') // comprehensive: 综合, latest: 最新, hot: 最热
const activeCategory = ref<string | null>(null)
const categories = ref<{ id: string; name: string; slug: string }[]>([])

// 排序选项
const sortOptions = [
  { key: 'comprehensive', label: '综合' },
  { key: 'latest', label: '最新' },
  { key: 'hot', label: '最热' },
]

// 获取分类列表
async function fetchCategories() {
  try {
    const { data } = await api.get('/categories')
    categories.value = data
  } catch {
    categories.value = []
  }
}

// 构建查询参数
function buildQuery() {
  const query: Record<string, string> = {}
  if (searchKeyword.value) query.search = searchKeyword.value
  if (activeCategory.value) query.category = activeCategory.value
  if (activeSort.value && activeSort.value !== 'comprehensive') query.sort = activeSort.value
  return query
}

// 执行搜索
async function doSearch() {
  const query = buildQuery()
  // 更新 URL
  router.replace({ query: Object.keys(query).length ? query : undefined })
  // 获取搜索结果
  await articleStore.fetchArticles(1, query)
}

// 处理页码变化
function handlePageChange(page: number) {
  const query = buildQuery()
  articleStore.fetchArticles(page, query)
}

// 选择分类
function selectCategory(slug: string | null) {
  activeCategory.value = activeCategory.value === slug ? null : slug
  doSearch()
}

// 选择排序
function selectSort(key: string) {
  activeSort.value = key
  doSearch()
}

// 清除搜索
function clearSearch() {
  searchKeyword.value = ''
  activeCategory.value = null
  activeSort.value = 'comprehensive'
  doSearch()
}

// 返回首页
function goBack() {
  router.push('/blog')
}

// 跳转文章详情
function goArticle(slug: string) {
  router.push(`/blog/${slug}`)
}

// 从 URL 同步搜索参数
function syncFromUrl() {
  const query = route.query
  searchKeyword.value = (query.search as string) || ''
  activeCategory.value = (query.category as string) || null
  activeSort.value = (query.sort as string) || 'comprehensive'
}

// 搜索结果数量文本
const resultCountText = computed(() => {
  if (!searchKeyword.value && !activeCategory.value) return ''
  return `共 ${articleStore.total} 个结果`
})

// 是否有筛选条件
const hasFilters = computed(() => {
  return searchKeyword.value || activeCategory.value || activeSort.value !== 'comprehensive'
})

onMounted(async () => {
  await fetchCategories()
  syncFromUrl()
  await doSearch()
})

// 监听 URL 变化
watch(() => route.query, () => {
  syncFromUrl()
})
</script>

<template>
  <div class="search-page">
    <!-- 顶部搜索栏 -->
    <div class="search-header">
      <div class="search-header-inner">
        <ElButton circle text class="back-btn" @click="goBack">
          <ElIcon :size="20"><ArrowLeft /></ElIcon>
        </ElButton>
        
        <div class="search-input-wrapper">
          <ElInput
            v-model="searchKeyword"
            placeholder="搜索文章..."
            clearable
            size="large"
            :prefix-icon="Search"
            @keyup.enter="doSearch"
          />
          <ElButton class="search-btn" type="primary" size="large" @click="doSearch">
            搜索
          </ElButton>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-bar-inner">
        <!-- 排序筛选 -->
        <div class="filter-section">
          <div class="filter-tabs">
            <button
              v-for="opt in sortOptions"
              :key="opt.key"
              class="filter-tab"
              :class="{ active: activeSort === opt.key }"
              @click="selectSort(opt.key)"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- 分类筛选 -->
        <div class="filter-section category-section">
          <span class="filter-label">分类：</span>
          <div class="filter-tags">
            <span
              class="filter-tag"
              :class="{ active: activeCategory === null }"
              @click="selectCategory(null)"
            >
              全部
            </span>
            <span
              v-for="cat in categories"
              :key="cat.id"
              class="filter-tag"
              :class="{ active: activeCategory === cat.slug }"
              @click="selectCategory(cat.slug)"
            >
              {{ cat.name }}
            </span>
          </div>
        </div>

        <!-- 清除筛选 -->
        <button v-if="hasFilters" class="clear-filter" @click="clearSearch">
          <ElIcon><Close /></ElIcon>
          清除筛选
        </button>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div class="search-results">
      <div class="results-inner">
        <!-- 结果统计 -->
        <div v-if="resultCountText" class="results-stats">
          {{ resultCountText }}
        </div>

        <!-- 加载状态 -->
        <ElSkeleton :loading="articleStore.loading" animated>
          <!-- 空状态 -->
          <div v-if="articleStore.articles.length === 0 && !articleStore.loading" class="empty-state">
            <ElEmpty :description="hasFilters ? '没有找到相关文章' : '请输入关键词搜索'" />
          </div>

          <!-- 结果列表 -->
          <div v-else class="article-list">
            <ElCard
              v-for="article in articleStore.articles"
              :key="article.id"
              shadow="hover"
              class="article-card"
              @click="goArticle(article.slug)"
            >
              <div class="article-layout">
                <div v-if="article.cover_url" class="article-cover">
                  <img :src="article.cover_url" :alt="article.title">
                </div>
                <div class="article-content">
                  <h3 class="article-title" v-html="article.title.replace(new RegExp(searchKeyword, 'gi'), match => `<mark>${match}</mark>`)" />
                  <p class="article-excerpt">{{ article.excerpt || '暂无摘要' }}</p>
                  <div class="article-meta">
                    <ElSpace size="small">
                      <ElTag v-if="article.category" size="small" type="info">{{ article.category.name }}</ElTag>
                      <ElTag v-for="tag in article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                    </ElSpace>
                    <ElText type="info" style="font-size: 12px">
                      {{ article.author.nickname || article.author.username }} · {{ new Date(article.published_at || article.created_at).toLocaleDateString() }}
                      · 阅读 {{ article.view_count }}
                    </ElText>
                  </div>
                </div>
              </div>
            </ElCard>
          </div>
        </ElSkeleton>

        <!-- 分页 -->
        <div v-if="articleStore.pages > 1" class="pagination">
          <ElPagination
            :current-page="articleStore.page"
            :page-count="articleStore.pages"
            layout="prev, pager, next"
            @update:current-page="handlePageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  min-height: 100vh;
  background: #f9f9f9;
}

.dark .search-page {
  background: var(--bg-primary);
}

/* 顶部搜索栏 */
.search-header {
  background: #f9f9f9;
  padding: 16px 0;
  position: sticky;
  top: 56px;
  z-index: 99;
}

.dark .search-header {
  background: var(--bg-primary);
}

.search-header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  position: relative;
}

.back-btn {
  flex-shrink: 0;
  position: absolute;
  left: 16px;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  max-width: 600px;
  margin: 0 auto;
  position: relative;
}

.search-input-wrapper :deep(.el-input) {
  flex: 1;
}

.search-input-wrapper :deep(.el-input__wrapper) {
  padding-right: 84px;
}

.search-btn {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
  height: 32px;
  padding: 0 16px;
}

/* 筛选栏 */
.filter-bar {
  background: #f9f9f9;
  padding: 12px 0;
}

.dark .filter-bar {
  background: var(--bg-primary);
}

.filter-bar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.filter-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: 12px;
}

.filter-section:first-child {
  border-bottom: 1px solid #e8e8e8;
}

.dark .filter-section:first-child {
  border-bottom-color: var(--border-color);
}

.filter-section:not(:first-child) {
  padding-top: 12px;
}

.filter-section:last-child {
  padding-bottom: 0;
}

/* 排序标签 */
.filter-tabs {
  display: flex;
  gap: 8px;
}

.filter-tab {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tab:hover {
  color: #18a058;
  background: #f5f7fa;
}

.filter-tab.active {
  color: #18a058;
  font-weight: 500;
  background: #e6f7ee;
}

.dark .filter-tab {
  color: var(--text-secondary);
}

.dark .filter-tab:hover {
  color: #4ade80;
  background: var(--bg-hover);
}

.dark .filter-tab.active {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
}

/* 分类筛选 */
.filter-label {
  font-size: 14px;
  color: #999;
  flex-shrink: 0;
}

.dark .filter-label {
  color: var(--text-tertiary);
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  color: #666;
  background: #f9f9f9;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.filter-tag:hover {
  color: #18a058;
  background: #e6f7ee;
}

.filter-tag.active {
  color: #18a058;
  background: #e6f7ee;
  border-color: #18a058;
}

.dark .filter-tag {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

.dark .filter-tag:hover {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
}

.dark .filter-tag.active {
  color: #4ade80;
  background: rgba(74, 222, 128, 0.15);
  border-color: #4ade80;
}

/* 清除筛选 */
.clear-filter {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  font-size: 13px;
  color: #999;
  background: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.clear-filter:hover {
  color: #f56c6c;
  border-color: #f56c6c;
}

.dark .clear-filter {
  color: var(--text-tertiary);
  border-color: var(--border-color);
}

.dark .clear-filter:hover {
  color: #f87171;
  border-color: #f87171;
}

/* 搜索结果 */
.search-results {
  padding: 24px 0;
}

.results-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.results-stats {
  font-size: 14px;
  color: #999;
  margin-bottom: 16px;
}

.dark .results-stats {
  color: var(--text-tertiary);
}

.empty-state {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 文章列表 */
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

.article-layout {
  display: flex;
  gap: 16px;
}

.article-cover {
  flex-shrink: 0;
  width: 200px;
  height: 120px;
  border-radius: 4px;
  overflow: hidden;
}

.article-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.article-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.article-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.4;
  color: #333;
}

.dark .article-title {
  color: var(--text-primary);
}

.article-title :deep(mark) {
  background: #ffeb3b;
  color: #333;
  padding: 0 2px;
}

.article-excerpt {
  flex: 1;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
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

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .search-header {
    top: 0;
  }

  .search-input-wrapper {
    max-width: none;
  }

  .article-layout {
    flex-direction: column;
  }

  .article-cover {
    width: 100%;
    height: 180px;
  }

  .filter-section {
    gap: 4px;
  }

  .filter-tab {
    padding: 6px 12px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .search-header-inner {
    padding: 0 12px;
  }

  .search-input-wrapper :deep(.el-button) {
    padding: 0 16px;
  }

  .results-inner {
    padding: 0 12px;
  }

  .article-title {
    font-size: 16px;
  }

  .article-excerpt {
    font-size: 13px;
  }
}
</style>
