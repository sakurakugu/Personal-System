<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, clearTimeout, Blob, URL, IntersectionObserver */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElCard, ElEmpty, ElIcon, ElMessage, ElPopconfirm, ElSkeleton, ElSpace, ElTag } from 'element-plus'
import { Document, Download, View } from '@element-plus/icons-vue'
import BaseDialog from '../../components/BaseDialog.vue'
import { deleteArticle as removeArticle, fetchMyArticleById, fetchMyArticleList } from '../../features/articles/api'
import { buildArticleTransferPayload } from '../../features/articles/transfer'
import type { ArticleListResponse, ArticleRecord } from '../../features/articles/types'
import ArticleCoverImage from '../../components/ArticleCoverImage.vue'
import { getApiErrorMessage } from '../../utils/api'

const router = useRouter()
const pageContainerRef = ref<globalThis.HTMLDivElement | null>(null)
const loadMoreTriggerRef = ref<globalThis.HTMLDivElement | null>(null)
const articles = ref<ArticleRecord[]>([])
const initialLoading = ref(true)
const refreshing = ref(false)
const loadingMore = ref(false)
const pagination = ref({ page: 0, pageSize: 10, total: 0, pageCount: 0 })
const showTransferDialog = ref(false)
const exportingArticles = ref(false)

const CREATE_BUTTON_LONG_PRESS_MS = 600
const ARTICLE_TRANSFER_VERSION = 1
const ARTICLE_EXPORT_PAGE_SIZE = 50
const ARTICLE_LIST_PAGE_SIZE = 10

let createButtonLongPressTimer: ReturnType<typeof setTimeout> | null = null
let ignoreNextCreateClick = false
let loadMoreObserver: IntersectionObserver | null = null

const exportArticleTotal = computed(() => pagination.value.total)
const hasMoreArticles = computed(() => pagination.value.page < pagination.value.pageCount)
const showSkeleton = computed(() => initialLoading.value && articles.value.length === 0)
const isArticleListEmpty = computed(() => !initialLoading.value && articles.value.length === 0)

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

function applyArticlePage(data: ArticleListResponse, append: boolean) {
  articles.value = append ? [...articles.value, ...data.items] : data.items
  pagination.value = { page: data.page, pageSize: data.page_size, total: data.total, pageCount: data.pages }
}

function disconnectLoadMoreObserver() {
  if (loadMoreObserver) {
    loadMoreObserver.disconnect()
    loadMoreObserver = null
  }
}

async function requestArticlePage(page: number, append: boolean) {
  const data = await fetchMyArticleList(page, pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE)
  applyArticlePage(data, append)
}

async function 获取指定可见数量的文章(targetVisibleCount: number) {
  const pageSize = pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE
  const firstPage = await fetchMyArticleList(1, pageSize)
  const items = [...firstPage.items]
  let currentPage = firstPage.page

  while (items.length < targetVisibleCount && currentPage < firstPage.pages) {
    currentPage += 1
    const data = await fetchMyArticleList(currentPage, pageSize)
    items.push(...data.items)
  }

  return {
    items,
    page: currentPage,
    pageSize: firstPage.page_size,
    total: firstPage.total,
    pageCount: firstPage.pages,
  }
}

async function reloadArticles(
  targetVisibleCount = ARTICLE_LIST_PAGE_SIZE,
  options: { silent?: boolean } = {},
) {
  const silent = options.silent ?? !initialLoading.value
  if (silent) {
    refreshing.value = true
  } else {
    initialLoading.value = true
  }
  loadingMore.value = false
  try {
    const data = await 获取指定可见数量的文章(targetVisibleCount)
    articles.value = data.items
    pagination.value = {
      page: data.page,
      pageSize: data.pageSize,
      total: data.total,
      pageCount: data.pageCount,
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载文章失败'))
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      initialLoading.value = false
    }
  }
}

async function fetchNextPage() {
  if (initialLoading.value || refreshing.value || loadingMore.value || !hasMoreArticles.value) {
    return
  }
  loadingMore.value = true
  try {
    await requestArticlePage(pagination.value.page + 1, true)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载更多文章失败'))
  } finally {
    loadingMore.value = false
  }
}

async function deleteArticle(id: string) {
  const targetVisibleCount = Math.max(articles.value.length - 1, pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE)
  await removeArticle(id)
  ElMessage.success('已删除')
  await reloadArticles(targetVisibleCount, { silent: true })
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
  void reloadArticles()
})

onBeforeUnmount(() => {
  clearCreateButtonLongPress()
  disconnectLoadMoreObserver()
})

watch(
  () => [pageContainerRef.value, loadMoreTriggerRef.value] as const,
  ([container, trigger]) => {
    disconnectLoadMoreObserver()
    if (!container || !trigger) {
      return
    }
    loadMoreObserver = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) {
          return
        }
        void fetchNextPage()
      },
      {
        root: container,
        rootMargin: '0px 0px 240px 0px',
      },
    )
    loadMoreObserver.observe(trigger)
  },
  { flush: 'post' },
)
</script>

<template>
  <div ref="pageContainerRef" class="page-container">
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

    <ElSkeleton :loading="showSkeleton" animated>
      <div v-loading="refreshing" class="article-list">
        <ElCard v-for="article in articles" :key="article.id" shadow="hover" class="article-card">
          <div class="article-card-inner">
            <div v-if="article.cover_url" class="article-cover">
              <ArticleCoverImage :url="article.cover_url" :alt="article.title" />
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
                    <ElPopconfirm
                      :title="`确定删除文章《${article.title || '未命名'}》？`"
                      confirm-button-text="确定"
                      cancel-button-text="取消"
                      @confirm="deleteArticle(article.id)"
                    >
                      <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
                    </ElPopconfirm>
                  </ElSpace>
                </div>
              </div>
            </div>
          </div>
        </ElCard>

        <ElEmpty v-if="isArticleListEmpty" description="还没有文章" />

        <div
          v-if="articles.length > 0 && hasMoreArticles"
          ref="loadMoreTriggerRef"
          class="article-load-trigger"
          aria-hidden="true"
        />
        <div v-if="loadingMore" class="article-list-status">
          正在加载更早的文章...
        </div>
        <div v-else-if="articles.length > 0 && !hasMoreArticles" class="article-list-status article-list-status--end">
          已显示全部文章
        </div>
      </div>
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
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.article-load-trigger {
  height: 1px;
}

.article-list-status {
  padding: 4px 0 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  text-align: center;
}

.article-list-status--end {
  color: var(--el-text-color-placeholder);
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
