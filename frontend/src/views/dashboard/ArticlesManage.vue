<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NButton, NTag, NSpace, NPopconfirm, useMessage, NSpin } from 'naive-ui'
import { ElIcon } from 'element-plus'
import { Document, View } from '@element-plus/icons-vue'
import api from '../../utils/api'

const router = useRouter()
const message = useMessage()
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
  message.success('已删除')
  await fetchArticles(pagination.value.page)
}

onMounted(() => fetchArticles())
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2 style="display: flex; align-items: center; gap: 8px">
        <ElIcon><Document /></ElIcon>
        <span>我的文章</span>
      </h2>
      <NButton type="primary" @click="router.push('/dashboard/articles/edit')">+ 写文章</NButton>
    </div>

    <NSpin :show="loading">
      <NCard v-for="article in articles" :key="article.id" size="small" style="margin-bottom: 8px" hoverable>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <div>
            <strong>{{ article.title }}</strong>
            <NSpace size="small" style="margin-top: 4px">
              <NTag :type="article.status === 'published' ? 'success' : 'default'" size="tiny">
                {{ article.status === 'published' ? '已发布' : '草稿' }}
              </NTag>
              <span style="font-size: 12px; color: #999; display: inline-flex; align-items: center; gap: 4px">
                <ElIcon><View /></ElIcon>
                <span>{{ article.view_count }} · {{ new Date(article.created_at).toLocaleDateString() }}</span>
              </span>
            </NSpace>
          </div>
          <NSpace size="small">
            <NButton size="tiny" @click="router.push(`/dashboard/articles/edit/${article.id}`)">编辑</NButton>
            <NPopconfirm @positive-click="deleteArticle(article.id)">
              <template #trigger><NButton size="tiny" type="error" quaternary>删除</NButton></template>
              确定删除这篇文章？
            </NPopconfirm>
          </NSpace>
        </div>
      </NCard>
    </NSpin>
  </div>
</template>
