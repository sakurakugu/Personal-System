<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElCard, ElIcon, ElMessage, ElPopconfirm, ElSkeleton, ElSpace, ElTag } from 'element-plus'
import { Document, View } from '@element-plus/icons-vue'
import { deleteArticle as removeArticle, fetchMyArticleList } from '../../features/articles/api'
import type { ArticleRecord } from '../../features/articles/types'

const router = useRouter()
const articles = ref<ArticleRecord[]>([])
const loading = ref(true)
const pagination = ref({ page: 1, pageSize: 10, total: 0, pageCount: 0 })

function getStatusType(status: ArticleRecord['status']): 'success' | 'warning' | 'info' {
  if (status === 'public') return 'success'
  if (status === 'login_required') return 'warning'
  return 'info'
}

function getStatusLabel(status: ArticleRecord['status']): string {
  if (status === 'public') return '公开'
  if (status === 'login_required') return '登录可见'
  return '私有'
}

async function fetchArticles(page = 1) {
  loading.value = true
  try {
    const data = await fetchMyArticleList(page)
    articles.value = data.items
    pagination.value = { page: data.page, pageSize: data.page_size, total: data.total, pageCount: data.pages }
  } finally {
    loading.value = false
  }
}

async function deleteArticle(id: string) {
  await removeArticle(id)
  ElMessage.success('已删除')
  await fetchArticles(pagination.value.page)
}

onMounted(() => fetchArticles())
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <ElIcon><Document /></ElIcon>
        <span>我的文章</span>
      </h2>
      <ElButton type="primary" @click="router.push('/dashboard/articles/edit')">+ 写文章</ElButton>
    </div>

    <ElSkeleton :loading="loading" animated>
      <ElCard v-for="article in articles" :key="article.id" shadow="hover" class="article-card">
        <div class="article-card-inner">
          <div v-if="article.cover_url" class="article-cover">
            <img :src="article.cover_url" :alt="article.title">
          </div>

          <div class="article-body">
            <div class="article-header">
              <h3 class="article-title">{{ article.title }}</h3>
              <ElTag :type="getStatusType(article.status)" size="small" effect="dark" class="article-status-tag">
                {{ getStatusLabel(article.status) }}
              </ElTag>
            </div>
            <p class="article-excerpt">{{ article.excerpt || '暂无摘要' }}</p>
            <div class="article-meta">
              <div class="article-meta-main">
                <ElSpace size="small">
                  <ElTag v-if="article.category" size="small" type="info">{{ article.category.name }}</ElTag>
                  <ElTag v-for="tag in article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                </ElSpace>
                <span class="article-meta-text">
                  <span>{{ new Date(article.published_at || article.created_at).toLocaleDateString() }}</span>
                  <span>·</span>
                  <span class="article-view">
                    <ElIcon><View /></ElIcon>
                    <span>{{ article.view_count }}</span>
                  </span>
                </span>
              </div>
              <div class="article-actions">
                <ElSpace size="small">
                  <ElButton size="small" @click="router.push(`/dashboard/articles/edit/${article.id}`)">编辑</ElButton>
                  <ElPopconfirm @confirm="deleteArticle(article.id)">
                    <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
                    确定删除这篇文章？
                  </ElPopconfirm>
                </ElSpace>
              </div>
            </div>
          </div>
        </div>
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
@import '../../styles/media.css';

.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.article-card {
  margin-bottom: 12px;
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.article-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.article-card-inner {
  position: relative;
}

.article-actions {
  margin-left: auto;
}

.article-cover {
  margin-bottom: 12px;
}

.article-cover img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
}

.article-title {
  margin: 0;
  font-size: 20px;
  line-height: 1.4;
}

.article-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.article-status-tag {
  flex: 0 0 auto;
}

.article-excerpt {
  margin: 0 0 12px;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  line-clamp: 2;
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

.article-meta-main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.article-meta-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #999;
  font-size: 12px;
}

.article-view {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

@media (--mobile-viewport) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .article-card-inner {
    padding-top: 0;
  }

  .article-header {
    flex-wrap: wrap;
  }
}
</style>
