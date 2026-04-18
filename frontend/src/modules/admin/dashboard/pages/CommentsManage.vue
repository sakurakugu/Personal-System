<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  ElButton,
  ElCard,
  ElEmpty,
  ElIcon,
  ElMessage,
  ElMessageBox,
  ElSpace,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { ChatDotRound, Check, Close } from '@element-plus/icons-vue'
import { fetchPendingComments as requestPendingComments, moderateComment } from '../../api'
import type { PendingComment } from '../../types'
import { getApiErrorMessage } from '../../../../shared/api'

const loading = ref(false)
const comments = ref<PendingComment[]>([])

const hasComments = computed(() => comments.value.length > 0)

async function fetchPendingComments() {
  loading.value = true
  try {
    comments.value = await requestPendingComments()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '获取待审核评论失败'))
  } finally {
    loading.value = false
  }
}

async function approveComment(comment: PendingComment) {
  try {
    await moderateComment(comment.id, 'approved')
    comments.value = comments.value.filter((item) => item.id !== comment.id)
    ElMessage.success('评论已通过')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '操作失败'))
  }
}

async function rejectComment(comment: PendingComment) {
  try {
    await ElMessageBox.confirm(
      '确定要拒绝这条评论吗？拒绝后评论将被删除。',
      '确认拒绝',
      { type: 'warning' }
    )
    await moderateComment(comment.id, 'rejected')
    comments.value = comments.value.filter((item) => item.id !== comment.id)
    ElMessage.success('评论已拒绝')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getApiErrorMessage(error, '操作失败'))
    }
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function getCommenterName(comment: PendingComment) {
  if (comment.user) {
    return comment.user.nickname || comment.user.username
  }
  return comment.guest_name || '匿名'
}

function getArticleTitle(comment: PendingComment) {
  return comment.article?.title || '文章已删除'
}

function getArticleLink(comment: PendingComment) {
  if (!comment.article) {
    return null
  }
  return `/blog/${comment.article.slug}`
}

onMounted(() => {
  void fetchPendingComments()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <span class="page-title-text">
          <ElIcon><ChatDotRound /></ElIcon>
          <span>评论审核</span>
        </span>
      </h2>
    </div>

    <ElCard class="comments-card">
      <div class="comments-body">
        <div class="comments-table-wrap desktop-view">
          <ElTable v-loading="loading" :data="comments" stripe height="100%">
            <template #empty>
              <ElEmpty description="暂无待审核的评论" />
            </template>
            <ElTableColumn type="index" width="50" />
            <ElTableColumn label="评论者" width="120">
              <template #default="{ row }">
                <div class="comment-author-cell">
                  <ElTag v-if="row.user" size="small" type="success" class="comment-role-tag">用户</ElTag>
                  <ElTag v-else size="small" type="info" class="comment-role-tag">游客</ElTag>
                  <div class="comment-author-name comment-author-name--inline">
                    {{ getCommenterName(row) }}
                  </div>
                </div>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="content" label="评论内容" min-width="300">
              <template #default="{ row }">
                <div class="comment-content">
                  {{ row.content }}
                </div>
              </template>
            </ElTableColumn>
            <ElTableColumn label="所属文章" min-width="200">
              <template #default="{ row }">
                <router-link
                  v-if="row.article"
                  :to="getArticleLink(row)!"
                  target="_blank"
                  class="article-link"
                >
                  {{ getArticleTitle(row) }}
                </router-link>
                <span v-else class="article-missing">{{ getArticleTitle(row) }}</span>
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
        </div>

        <div class="comments-mobile-wrap mobile-view">
          <div v-loading="loading" class="comment-card-list">
            <ElCard
              v-for="comment in comments"
              :key="comment.id"
              class="comment-card"
            >
              <div class="comment-card-header">
                <div class="comment-card-author">
                  <ElTag v-if="comment.user" size="small" type="success" class="comment-role-tag">用户</ElTag>
                  <ElTag v-else size="small" type="info" class="comment-role-tag">游客</ElTag>
                  <span class="comment-card-author-name">{{ getCommenterName(comment) }}</span>
                </div>
                <span class="comment-card-time">{{ formatDate(comment.created_at) }}</span>
              </div>

              <div class="comment-card-section">
                <div class="comment-card-label">评论内容</div>
                <div class="comment-card-content">
                  {{ comment.content }}
                </div>
              </div>

              <div class="comment-card-section">
                <div class="comment-card-label">所属文章</div>
                <router-link
                  v-if="comment.article"
                  :to="getArticleLink(comment)!"
                  target="_blank"
                  class="article-link article-link--card"
                >
                  {{ getArticleTitle(comment) }}
                </router-link>
                <span v-else class="article-missing">
                  {{ getArticleTitle(comment) }}
                </span>
              </div>

              <div class="comment-card-actions">
                <ElButton
                  type="success"
                  size="small"
                  :icon="Check"
                  @click="approveComment(comment)"
                >
                  通过
                </ElButton>
                <ElButton
                  type="danger"
                  size="small"
                  :icon="Close"
                  @click="rejectComment(comment)"
                >
                  拒绝
                </ElButton>
              </div>
            </ElCard>

            <ElEmpty v-if="!hasComments && !loading" description="暂无待审核的评论" />
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
@import '../../../../styles/media.css';

.page-container {
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0;
}

.page-title-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.comments-card {
  flex: 1;
  min-height: 0;
  border-radius: var(--dashboard-panel-radius, 12px);
  overflow: hidden;
}

.comments-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.comments-body {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.desktop-view {
  display: block;
}

.mobile-view {
  display: none;
}

.comments-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.comments-table-wrap :deep(.el-table) {
  height: 100%;
}

.comments-table-wrap :deep(.el-table__cell) {
  vertical-align: top;
}

.comment-author-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.comment-role-tag {
  width: fit-content;
  max-width: 100%;
  flex-shrink: 0;
}

.comment-author-name {
  font-weight: 500;
}

.comment-author-name--inline {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.comment-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.article-link {
  color: var(--el-color-primary);
  text-decoration: none;
}

.article-link:hover {
  text-decoration: underline;
}

.article-missing {
  color: var(--el-text-color-secondary);
}

.comments-mobile-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.comment-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

.comment-card {
  border-radius: 12px;
  border-left: 3px solid var(--el-color-primary);
}

.comment-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 16px;
}

.comment-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.comment-card-author {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.comment-card-author-name {
  min-width: 0;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.comment-card-time {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.comment-card-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comment-card-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.comment-card-content {
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--el-text-color-primary);
}

.article-link--card,
.article-missing {
  line-height: 1.5;
  word-break: break-word;
}

.comment-card-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

@media (--mobile-viewport) {
  .page-container {
    padding: 24px;
    gap: 12px;
  }

  .desktop-view {
    display: none;
  }

  .mobile-view {
    display: block;
  }
}
</style>

