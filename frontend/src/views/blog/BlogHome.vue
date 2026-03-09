<script setup lang="ts">
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
import { ElIcon } from 'element-plus'
import { HomeFilled, View } from '@element-plus/icons-vue'
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useArticleStore } from '../../stores/article'
import api from '../../utils/api'

const articleStore = useArticleStore()
const router = useRouter()

const search = ref('')
const categoryFilter = ref<string | null>(null)
const categories = ref<{ id: string; name: string; slug: string }[]>([])

onMounted(async () => {
  await articleStore.fetchArticles()
  try {
    const { data } = await api.get('/categories')
    categories.value = data
  } catch {}
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
    <div class="blog-hero">
      <h1 style="display: inline-flex; align-items: center; gap: 8px">
        <ElIcon><HomeFilled /></ElIcon>
        <span>Sakurakuguの小窝</span>
      </h1>
      <p>记录生活，分享技术</p>
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
      <div v-if="articleStore.articles.length === 0 && !articleStore.loading" style="padding: 60px 0">
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
          <div class="article-cover" v-if="article.cover_url">
            <img :src="article.cover_url" :alt="article.title" />
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
                {{ article.author.username }} · {{ new Date(article.published_at || article.created_at).toLocaleDateString() }}
                ·
                <ElIcon style="vertical-align: middle"><View /></ElIcon>
                {{ article.view_count }}
              </NText>
            </div>
          </div>
        </NCard>
      </div>
    </NSpin>

    <div class="pagination" v-if="articleStore.pages > 1">
      <NPagination
        :page="articleStore.page"
        :page-count="articleStore.pages"
        @update:page="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.blog-home {
  max-width: 800px;
  margin: 0 auto;
}

.blog-hero {
  text-align: center;
  padding: 40px 0 24px;
}

.blog-hero h1 {
  font-size: 32px;
  margin-bottom: 8px;
}

.blog-hero p {
  color: #888;
  font-size: 16px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.article-card:hover {
  transform: translateY(-2px);
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
}

.article-excerpt {
  color: #666;
  font-size: 14px;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
</style>
