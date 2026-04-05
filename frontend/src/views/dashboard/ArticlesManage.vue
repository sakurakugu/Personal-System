<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, clearTimeout, Blob, URL */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElCard, ElIcon, ElMessage, ElPopconfirm, ElSkeleton, ElSpace, ElTag } from 'element-plus'
import { Document, Download, View } from '@element-plus/icons-vue'
import BaseDialog from '../../components/BaseDialog.vue'
import { deleteArticle as removeArticle, fetchMyArticleById, fetchMyArticleList } from '../../features/articles/api'
import { buildArticleTransferPayload } from '../../features/articles/transfer'
import type { ArticleRecord } from '../../features/articles/types'
import { getApiErrorMessage } from '../../utils/api'

const router = useRouter()
const articles = ref<ArticleRecord[]>([])
const loading = ref(true)
const pagination = ref({ page: 1, pageSize: 10, total: 0, pageCount: 0 })
const showTransferDialog = ref(false)
const exportingArticles = ref(false)

const CREATE_BUTTON_LONG_PRESS_MS = 600
const ARTICLE_TRANSFER_VERSION = 1
const ARTICLE_EXPORT_PAGE_SIZE = 50

let createButtonLongPressTimer: ReturnType<typeof setTimeout> | null = null
let ignoreNextCreateClick = false

const exportArticleTotal = computed(() => pagination.value.total)

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

function clearCreateButtonLongPress() {
  if (createButtonLongPressTimer !== null) {
    clearTimeout(createButtonLongPressTimer)
    createButtonLongPressTimer = null
  }
}

function openTransferDialog() {
  showTransferDialog.value = true
}

function startCreateButtonLongPress(event: Event) {
  if (event instanceof MouseEvent && event.button !== 0) {
    return
  }
  clearCreateButtonLongPress()
  createButtonLongPressTimer = setTimeout(() => {
    ignoreNextCreateClick = true
    openTransferDialog()
  }, CREATE_BUTTON_LONG_PRESS_MS)
}

function cancelCreateButtonLongPress() {
  clearCreateButtonLongPress()
}

function handleCreateButtonClick() {
  clearCreateButtonLongPress()
  if (ignoreNextCreateClick) {
    ignoreNextCreateClick = false
    return
  }
  void router.push('/dashboard/articles/edit')
}

async function fetchAllMyArticles(): Promise<ArticleRecord[]> {
  const firstPage = await fetchMyArticleList(1, ARTICLE_EXPORT_PAGE_SIZE)
  const summaryArticles = [...firstPage.items]

  for (let page = 2; page <= firstPage.pages; page += 1) {
    const data = await fetchMyArticleList(page, ARTICLE_EXPORT_PAGE_SIZE)
    summaryArticles.push(...data.items)
  }

  return Promise.all(summaryArticles.map((article) => fetchMyArticleById(article.id)))
}

function downloadBackupFile(filename: string, content: string) {
  const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function exportArticles() {
  exportingArticles.value = true
  try {
    const allArticles = await fetchAllMyArticles()
    if (allArticles.length === 0) {
      ElMessage.warning('当前没有可备份的文章')
      return
    }

    const payload = buildArticleTransferPayload(ARTICLE_TRANSFER_VERSION, allArticles)
    const today = new Date().toISOString().slice(0, 10)
    downloadBackupFile(`articles-${today}.json`, JSON.stringify(payload, null, 2))
    ElMessage.success(`已备份 ${payload.total} 篇文章`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '文章备份失败'))
  } finally {
    exportingArticles.value = false
  }
}

onMounted(() => {
  void fetchArticles()
})

onBeforeUnmount(() => {
  clearCreateButtonLongPress()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <ElIcon><Document /></ElIcon>
        <span>我的文章</span>
      </h2>
      <div class="page-actions">
        <ElButton plain @click="openTransferDialog">
          <ElIcon><Download /></ElIcon>
          <span>备份</span>
        </ElButton>
        <div
          class="create-button-wrapper"
          @touchstart.passive="startCreateButtonLongPress"
          @touchmove="cancelCreateButtonLongPress"
          @touchend="cancelCreateButtonLongPress"
          @touchcancel="cancelCreateButtonLongPress"
          @mousedown="startCreateButtonLongPress"
          @mouseup="cancelCreateButtonLongPress"
          @mouseleave="cancelCreateButtonLongPress"
          @contextmenu.prevent
        >
          <ElButton type="primary" title="长按可打开文章备份" @click="handleCreateButtonClick">+ 写文章</ElButton>
        </div>
      </div>
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

    <BaseDialog
      v-model="showTransferDialog"
      title="文章备份"
      width="460px"
      style="max-width: 90vw"
    >
      <div class="article-transfer-dialog">
        <div class="article-transfer-tip">
          长按“写文章”或点击“备份”可打开此弹窗。系统会自动拉取当前账号下的全部文章详情，并导出为 JSON 文件，包含正文、摘要、封面、可见性、分类、标签与时间信息。
        </div>
        <div class="article-transfer-count">
          当前可备份 {{ exportArticleTotal }} 篇文章
        </div>
        <ElButton class="article-transfer-action" type="primary" plain :loading="exportingArticles" @click="exportArticles">
          <span class="article-transfer-action-content">
            <span class="article-transfer-action-head">
              <ElIcon><Download /></ElIcon>
              <span class="article-transfer-action-label">完整备份</span>
            </span>
            <span class="article-transfer-action-desc">导出当前用户的全部文章详情为 JSON 文件，适合本地长期留档</span>
          </span>
        </ElButton>
        <div class="article-transfer-note">
          当前版本先提供导出备份，确保你能把所有文章正文完整留在本地。
        </div>
      </div>
    </BaseDialog>
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

.page-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.create-button-wrapper {
  display: flex;
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

.article-transfer-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-transfer-tip,
.article-transfer-note {
  color: var(--el-text-color-regular);
  font-size: 13px;
  line-height: 1.7;
}

.article-transfer-count {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.article-transfer-action {
  height: auto;
  min-height: 132px;
  margin-left: 0;
  padding: 18px 16px;
  justify-content: flex-start;
  white-space: normal;
  text-align: left;
}

.article-transfer-action:hover,
.article-transfer-action:focus-visible {
  transform: translateY(-1px);
}

.article-transfer-action-content {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.article-transfer-action-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.article-transfer-action-head .el-icon {
  font-size: 16px;
}

.article-transfer-action-label {
  font-size: 15px;
  font-weight: 600;
}

.article-transfer-action-desc {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.6;
}

@media (--mobile-viewport) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    justify-content: stretch;
  }

  .create-button-wrapper {
    flex: 1 1 0;
  }

  .page-actions :deep(.el-button) {
    flex: 1 1 0;
  }

  .article-card-inner {
    padding-top: 0;
  }

  .article-header {
    flex-wrap: wrap;
  }
}
</style>
