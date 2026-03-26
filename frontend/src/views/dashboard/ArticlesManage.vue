<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElCard, ElIcon, ElMessage, ElPopconfirm, ElSkeleton, ElSpace, ElTag } from 'element-plus'
import { Document, View } from '@element-plus/icons-vue'
import api from '../../utils/api'

const router = useRouter()
const articles = ref<any[]>([])
const loading = ref(true)
const pagination = ref({ page: 1, pageSize: 10, total: 0, pageCount: 0 })

async function fetchArticles(page = 1) {
  loading.value = true
  try {
    const { data } = await api.get('/articles/my/list', { params: { page, page_size: 10 } })
    articles.value = data.items
    pagination.value = { page: data.page, pageSize: data.page_size, total: data.total, pageCount: data.pages }
  } finally {
    loading.value = false
  }
}

async function deleteArticle(id: string) {
  await api.delete(`/articles/${id}`)
  ElMessage.success('已删除')
  await fetchArticles(pagination.value.page)
}

onMounted(() => fetchArticles())
</script>

<template>
  <div class="page-container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><Document /></ElIcon>
        <span>我的文章</span>
      </h2>
      <ElButton type="primary" @click="router.push('/dashboard/articles/edit')">+ 写文章</ElButton>
    </div>

    <ElSkeleton :loading="loading" animated>
      <ElCard v-for="article in articles" :key="article.id" shadow="hover" style="margin-bottom: 8px">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <div>
            <strong>{{ article.title }}</strong>
            <ElSpace size="small" style="margin-top: 4px">
              <ElTag :type="article.status === 'published' ? 'success' : 'info'" size="small">
                {{ article.status === 'published' ? '已发布' : '草稿' }}
              </ElTag>
              <span style="font-size: 12px; color: #999; display: inline-flex; align-items: center; gap: 4px">
                <ElIcon><View /></ElIcon>
                <span>{{ article.view_count }} · {{ new Date(article.created_at).toLocaleDateString() }}</span>
              </span>
            </ElSpace>
          </div>
          <ElSpace size="small">
            <ElButton size="small" @click="router.push(`/dashboard/articles/edit/${article.id}`)">编辑</ElButton>
            <ElPopconfirm @confirm="deleteArticle(article.id)">
              <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
              确定删除这篇文章？
            </ElPopconfirm>
          </ElSpace>
        </div>
      </ElCard>
    </ElSkeleton>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}
</style>
