<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElSpace,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { ChatDotRound, Check, Close } from '@element-plus/icons-vue'
import api from '../../utils/api'

interface PendingComment {
  id: string
  article_id: string
  article: { id: string; title: string; slug: string } | null
  content: string
  guest_name: string | null
  user: { username: string; nickname: string | null } | null
  created_at: string
}

const loading = ref(false)
const comments = ref<PendingComment[]>([])

// 获取待审核评论
async function fetchPendingComments() {
  loading.value = true
  try {
    const { data } = await api.get('/comments/pending')
    comments.value = data
    console.log('待审核评论:', data)
  } catch (e: any) {
    console.error('获取待审核评论失败:', e)
    ElMessage.error(e.response?.data?.detail || '获取待审核评论失败')
  } finally {
    loading.value = false
  }
}

// 批准评论
async function approveComment(comment: PendingComment) {
  try {
    await api.patch(`/comments/${comment.id}/moderate`, { status: 'approved' })
    ElMessage.success('评论已通过')
    await fetchPendingComments()
  } catch {
    ElMessage.error('操作失败')
  }
}

// 拒绝评论
async function rejectComment(comment: PendingComment) {
  try {
    await ElMessageBox.confirm(
      '确定要拒绝这条评论吗？拒绝后评论将被删除。',
      '确认拒绝',
      { type: 'warning' }
    )
    await api.patch(`/comments/${comment.id}/moderate`, { status: 'rejected' })
    ElMessage.success('评论已拒绝')
    await fetchPendingComments()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 格式化日期
function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

// 获取评论者名称
function getCommenterName(comment: PendingComment) {
  if (comment.user) {
    return comment.user.nickname || comment.user.username
  }
  return comment.guest_name || '匿名'
}

onMounted(() => {
  fetchPendingComments()
})
</script>

<template>
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><ChatDotRound /></ElIcon>
      <span>评论审核</span>
    </h2>

    <ElCard>
      <ElTable v-loading="loading" :data="comments" stripe>
        <ElTableColumn type="index" width="50" />
        <ElTableColumn label="评论者" width="120">
          <template #default="{ row }">
            <ElTag v-if="row.user" size="small" type="success">用户</ElTag>
            <ElTag v-else size="small" type="info">游客</ElTag>
            <div style="margin-top: 4px; font-weight: 500">
              {{ getCommenterName(row) }}
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="content" label="评论内容" min-width="300">
          <template #default="{ row }">
            <div style="white-space: pre-wrap; word-break: break-word">
              {{ row.content }}
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="所属文章" min-width="200">
          <template #default="{ row }">
            <router-link
              v-if="row.article"
              :to="`/blog/${row.article.slug}`"
              target="_blank"
              style="color: var(--el-color-primary); text-decoration: none"
            >
              {{ row.article.title }}
            </router-link>
            <span v-else style="color: var(--el-text-color-secondary)">文章已删除</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="created_at" label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <ElSpace>
              <ElButton
                type="success"
                size="small"
                :icon="Check"
                @click="approveComment(row)"
              >
                通过
              </ElButton>
              <ElButton
                type="danger"
                size="small"
                :icon="Close"
                @click="rejectComment(row)"
              >
                拒绝
              </ElButton>
            </ElSpace>
          </template>
        </ElTableColumn>
      </ElTable>

      <div v-if="comments.length === 0 && !loading" style="padding: 40px 0">
        <ElEmpty description="暂无待审核的评论" />
      </div>
    </ElCard>
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
