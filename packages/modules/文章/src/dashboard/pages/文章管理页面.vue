<script setup lang="ts">
/* global Event, TouchEvent, MouseEvent, clearTimeout, Blob, URL, IntersectionObserver */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ElButton,
  ElCard,
  ElEmpty,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElIcon,
  ElInput,
  ElMessage,
  ElPopconfirm,
  ElSkeleton,
  ElSpace,
  ElSelect,
  ElOption,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { Delete, Document, Download, Grid, List } from '@element-plus/icons-vue'
import { BaseDialog, ContentTabs, PageSectionShell, type ContentTabItem } from '@personal-system/ui'
import {
  删除文章 as removeArticle,
  创建文章草稿,
  更新文章,
  文章转待办,
  文章转资料,
  全部文章筛选值,
  根据ID获取我的文章,
  获取我的文章分类列表,
  获取我的文章列表,
  恢复文章 as requestRestoreArticle,
  未分类文章筛选值,
} from '../../api'
import { 构建文章传输负载 } from '../../transfer'
import type { ArticleListResponse, ArticleRecord, CategoryRecord, ArticleOrganizationState } from '../../types'
import ArticleCoverImage from '../../components/文章封面图片.vue'
import { 获取API错误消息 } from '@personal-system/api'
import { 使用视口 } from '../../使用视口'

const props = withDefaults(defineProps<{
  showBack?: boolean
  backTo?: string
}>(), {
  showBack: false,
  backTo: '/',
})

const router = useRouter()
const route = useRoute()
const { isMobileViewport } = 使用视口()
const pageContainerRef = ref<globalThis.HTMLDivElement | null>(null)
const loadMoreTriggerRef = ref<globalThis.HTMLDivElement | null>(null)
const articles = ref<ArticleRecord[]>([])
const categories = ref<CategoryRecord[]>([])
const initialLoading = ref(true)
const refreshing = ref(false)
const loadingMore = ref(false)
const pagination = ref({ page: 0, pageSize: 10, total: 0, pageCount: 0 })
const allArticleTotal = ref(0)
const showTransferDialog = ref(false)
const exportingArticles = ref(false)
type ArticleListMode = 'active-card' | 'active-table' | 'deleted'
const currentListMode = ref<ArticleListMode>('active-table')
const selectedCategoryId = ref<string>(全部文章筛选值)
const selectedOrganizationState = ref<ArticleOrganizationState | ''>('')
const searchText = ref('')
const appliedSearch = ref('')
const quickContent = ref('')
const quickSaving = ref(false)
const showConvertDialog = ref(false)
const converting = ref(false)
const convertingArticle = ref<ArticleRecord | null>(null)
const convertTarget = ref<'todo' | 'material'>('todo')
const convertTitle = ref('')
const convertContent = ref('')
const convertNote = ref('')
const convertMaterialType = ref<'text' | 'link'>('text')

const CREATE_BUTTON_LONG_PRESS_MS = 600
const ARTICLE_TRANSFER_VERSION = 2
const ARTICLE_EXPORT_PAGE_SIZE = 50
const ARTICLE_LIST_PAGE_SIZE = 10

let createButtonLongPressTimer: ReturnType<typeof setTimeout> | null = null
let ignoreNextCreateClick = false
let loadMoreObserver: IntersectionObserver | null = null

const hasMoreArticles = computed(() => pagination.value.page < pagination.value.pageCount)
const showSkeleton = computed(() => initialLoading.value && articles.value.length === 0)
const isArticleListEmpty = computed(() => !initialLoading.value && articles.value.length === 0)
const isRecycleBinMode = computed(() => currentListMode.value === 'deleted')
const isTableViewMode = computed(() => currentListMode.value === 'active-table')
const activeCategoryId = computed(() => selectedCategoryId.value)
const articleTableTitleMinWidth = computed(() => (isMobileViewport.value ? 150 : 280))
const articleTableStatusWidth = computed(() => (isMobileViewport.value ? 84 : 98))
const articleTableActionWidth = computed(() => (isMobileViewport.value ? 156 : 180))
const exportArticleTotal = computed(() => (isRecycleBinMode.value ? 0 : allArticleTotal.value))
const emptyDescription = computed(() => (isRecycleBinMode.value ? '回收站里还没有文章' : '还没有文章'))
const 路由前缀 = computed(() => route.path.startsWith('/dashboard') ? '/dashboard' : '')
const uncategorizedArticleTotal = computed(() => {
  const categorizedTotal = categories.value.reduce((total, category) => total + (category.article_count ?? 0), 0)
  return Math.max(allArticleTotal.value - categorizedTotal, 0)
})
const articleListModeOptions = [
  { value: 'active-table', label: '列表', icon: List },
  { value: 'active-card', label: '卡片', icon: Grid },
  { value: 'deleted', label: '回收站', icon: Delete },
] as const satisfies readonly { value: ArticleListMode, label: string, icon: typeof List }[]

const categoryFilterOptions = computed<ContentTabItem[]>(() => [
  { value: 全部文章筛选值, label: '全部', count: allArticleTotal.value },
  ...(uncategorizedArticleTotal.value > 0
    ? [{ value: 未分类文章筛选值, label: '未分类', count: uncategorizedArticleTotal.value }]
    : []),
  ...categories.value.map((category) => ({
    value: category.id,
    label: category.name,
    count: category.article_count ?? 0,
  })),
])

function 是否回收站列表模式(mode: ArticleListMode | undefined) {
  return mode === 'deleted'
}

function resolve文章路径(path: '/articles' | '/articles/edit', articleId?: string) {
  const fullPath = `${路由前缀.value}${path}`
  return articleId ? `${fullPath}/${articleId}` : fullPath
}

function getStatusType(status: ArticleRecord['status']): 'success' | 'warning' | 'info' {
  if (status === 'public') return 'success'
  if (status === 'login_required') return 'warning'
  return 'info'
}

function getStatusLabel(status: ArticleRecord['status']): string {
  if (status === 'public') return '公开'
  if (status === 'login_required') return '登录可见'
  return '未发布'
}

function formatArticleDate(date: string | null) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

function formatArticleDateTime(date: string | null) {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

function formatArticleWordCount(count: number | null | undefined) {
  return `${Math.max(0, count ?? 0).toLocaleString()} 字`
}

function getArticlePublishDate(article: ArticleRecord) {
  return formatArticleDate(article.created_at)
}

function getArticleEditDate(article: ArticleRecord) {
  return formatArticleDateTime(article.last_edited_at || article.updated_at || article.created_at)
}

function applyArticlePage(data: ArticleListResponse, append: boolean) {
  articles.value = append ? [...articles.value, ...data.items] : data.items
  pagination.value = { page: data.page, pageSize: data.page_size, total: data.total, pageCount: data.pages }
}

function 重置无效分类筛选() {
  if (selectedCategoryId.value === 未分类文章筛选值 && uncategorizedArticleTotal.value <= 0) {
    selectedCategoryId.value = 全部文章筛选值
    return
  }
  if (
    selectedCategoryId.value !== 全部文章筛选值
    && selectedCategoryId.value !== 未分类文章筛选值
    && !categories.value.some((category) => category.id === selectedCategoryId.value)
  ) {
    selectedCategoryId.value = 全部文章筛选值
  }
}

async function reloadCategories() {
  categories.value = await 获取我的文章分类列表(isRecycleBinMode.value)
  重置无效分类筛选()
}

function disconnectLoadMoreObserver() {
  if (loadMoreObserver) {
    loadMoreObserver.disconnect()
    loadMoreObserver = null
  }
}

async function requestArticlePage(page: number, append: boolean) {
  const data = await 获取我的文章列表(
    page,
    pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE,
    isRecycleBinMode.value,
    activeCategoryId.value,
    selectedOrganizationState.value || undefined,
    appliedSearch.value || undefined,
  )
  applyArticlePage(data, append)
}

async function 获取指定可见数量的文章(targetVisibleCount: number) {
  const pageSize = pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE
  const firstPage = await 获取我的文章列表(1, pageSize, isRecycleBinMode.value, activeCategoryId.value, selectedOrganizationState.value || undefined, appliedSearch.value || undefined)
  const items = [...firstPage.items]
  let currentPage = firstPage.page

  while (items.length < targetVisibleCount && currentPage < firstPage.pages) {
    currentPage += 1
    const data = await 获取我的文章列表(currentPage, pageSize, isRecycleBinMode.value, activeCategoryId.value, selectedOrganizationState.value || undefined, appliedSearch.value || undefined)
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

async function 刷新全部文章数量(totalFromCurrentPage?: number) {
  if (activeCategoryId.value === 全部文章筛选值 && !selectedOrganizationState.value && !appliedSearch.value && typeof totalFromCurrentPage === 'number') {
    allArticleTotal.value = totalFromCurrentPage
    return
  }

  const data = await 获取我的文章列表(1, 1, isRecycleBinMode.value, 全部文章筛选值)
  allArticleTotal.value = data.total
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
    await 刷新全部文章数量(data.total)
    articles.value = data.items
    pagination.value = {
      page: data.page,
      pageSize: data.pageSize,
      total: data.total,
      pageCount: data.pageCount,
    }
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载文章失败'))
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
    ElMessage.error(获取API错误消息(error, '加载更多文章失败'))
  } finally {
    loadingMore.value = false
  }
}

async function deleteArticle(id: string) {
  const targetVisibleCount = Math.max(articles.value.length - 1, pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE)
  await removeArticle(id, isRecycleBinMode.value)
  ElMessage.success(isRecycleBinMode.value ? '已永久删除' : '已移入回收站')
  await reloadCategories()
  await reloadArticles(targetVisibleCount, { silent: true })
}

async function restoreArticle(id: string) {
  const targetVisibleCount = Math.max(articles.value.length - 1, pagination.value.pageSize || ARTICLE_LIST_PAGE_SIZE)
  await requestRestoreArticle(id)
  ElMessage.success('已恢复文章')
  await reloadCategories()
  await reloadArticles(targetVisibleCount, { silent: true })
}

async function saveQuickArticle() {
  const content = quickContent.value.trim()
  if (!content) return
  quickSaving.value = true
  try {
    await 创建文章草稿({ content, organization_state: 'inbox' })
    quickContent.value = ''
    ElMessage.success('已存入待整理')
    await reloadCategories()
    await reloadArticles(ARTICLE_LIST_PAGE_SIZE, { silent: true })
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '保存失败'))
  } finally {
    quickSaving.value = false
  }
}

async function changeOrganizationState(article: ArticleRecord, state: ArticleOrganizationState) {
  if (article.organization_state === state) return
  try {
    await 更新文章(article.id, { organization_state: state })
    ElMessage.success('整理状态已更新')
    await reloadArticles(Math.max(articles.value.length, ARTICLE_LIST_PAGE_SIZE), { silent: true })
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '更新整理状态失败'))
  }
}

async function openConvertDialog(article: ArticleRecord, target: 'todo' | 'material') {
  convertingArticle.value = article
  convertTarget.value = target
  convertTitle.value = article.title
  convertContent.value = article.excerpt || ''
  convertNote.value = ''
  convertMaterialType.value = 'text'
  try {
    const detail = await 根据ID获取我的文章(article.id)
    if (convertingArticle.value?.id !== article.id) return
    convertContent.value = detail.content
    showConvertDialog.value = true
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '读取文章正文失败'))
  }
}

async function submitConversion() {
  const article = convertingArticle.value
  if (!article || !convertTitle.value.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  converting.value = true
  try {
    if (convertTarget.value === 'todo') {
      await 文章转待办(article.id, { title: convertTitle.value.trim(), description: convertContent.value || null })
    } else {
      await 文章转资料(article.id, { title: convertTitle.value.trim(), content_text: convertContent.value || null, note: convertNote.value || null, type: convertMaterialType.value })
    }
    showConvertDialog.value = false
    ElMessage.success(convertTarget.value === 'todo' ? '已生成待办' : '已生成资料')
    await reloadArticles(Math.max(articles.value.length, ARTICLE_LIST_PAGE_SIZE), { silent: true })
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '转换失败'))
  } finally {
    converting.value = false
  }
}

function targetRoute(target: 'todo' | 'material', id: string) {
  return `${路由前缀.value}/${target === 'todo' ? 'todos' : 'materials'}?open=${encodeURIComponent(id)}`
}

function handleArticleAction(article: ArticleRecord, action: string) {
  if (action === 'todo' || action === 'material') openConvertDialog(article, action)
  if (action === 'inbox' || action === 'organized' || action === 'archived') void changeOrganizationState(article, action)
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
  void router.push(resolve文章路径('/articles/edit'))
}

async function fetchAllMyArticles(): Promise<ArticleRecord[]> {
  const firstPage = await 获取我的文章列表(1, ARTICLE_EXPORT_PAGE_SIZE)
  const summaryArticles = [...firstPage.items]

  for (let page = 2; page <= firstPage.pages; page += 1) {
    const data = await 获取我的文章列表(page, ARTICLE_EXPORT_PAGE_SIZE)
    summaryArticles.push(...data.items)
  }

  return Promise.all(summaryArticles.map((article) => 根据ID获取我的文章(article.id)))
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

    const payload = 构建文章传输负载(ARTICLE_TRANSFER_VERSION, allArticles)
    const today = new Date().toISOString().slice(0, 10)
    downloadBackupFile(`articles-${today}.json`, JSON.stringify(payload, null, 2))
    ElMessage.success(`已备份 ${payload.total} 篇文章`)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '文章备份失败'))
  } finally {
    exportingArticles.value = false
  }
}

onMounted(() => {
  void reloadCategories()
  void reloadArticles()
})

onBeforeUnmount(() => {
  clearCreateButtonLongPress()
  disconnectLoadMoreObserver()
})

watch(
  () => [currentListMode.value, selectedCategoryId.value, selectedOrganizationState.value, appliedSearch.value] as const,
  ([nextMode, nextCategoryId, nextState, nextSearch], [previousMode, previousCategoryId, previousState, previousSearch]) => {
    if (
      是否回收站列表模式(nextMode) === 是否回收站列表模式(previousMode)
      && nextCategoryId === previousCategoryId
      && nextState === previousState
      && nextSearch === previousSearch
    ) {
      return
    }
    pagination.value = { page: 0, pageSize: 10, total: 0, pageCount: 0 }
    if (是否回收站列表模式(nextMode) !== 是否回收站列表模式(previousMode)) {
      void reloadCategories()
    }
    void reloadArticles(ARTICLE_LIST_PAGE_SIZE, { silent: true })
  },
)

watch(
  () => [uncategorizedArticleTotal.value, categories.value] as const,
  () => {
    重置无效分类筛选()
  },
)

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
    <PageSectionShell
      title="文章管理"
      :icon="Document"
      title-tag="h2"
      :show-back="props.showBack"
      :to="props.backTo"
    >
      <template #header-extra>
        <div class="page-actions">
          <div class="article-mode-nav" aria-label="文章视图切换">
            <button
              v-for="item in articleListModeOptions"
              :key="item.value"
              class="article-mode-nav__item"
              :class="{ 'is-active': currentListMode === item.value }"
              type="button"
              :title="item.label"
              @click="currentListMode = item.value"
            >
              <ElIcon><component :is="item.icon" /></ElIcon>
              <span>{{ item.label }}</span>
            </button>
          </div>
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
      </template>

      <ElSkeleton :loading="showSkeleton" animated>
        <div v-loading="refreshing" class="article-list">
          <div v-if="!isRecycleBinMode" class="article-quick-entry">
            <ElInput v-model="quickContent" type="textarea" :rows="2" placeholder="快速记录想法或信息" maxlength="20000" show-word-limit />
            <ElButton type="primary" :loading="quickSaving" :disabled="!quickContent.trim()" @click="saveQuickArticle">存入待整理</ElButton>
          </div>
          <div class="article-filters">
            <ElSelect v-if="!isRecycleBinMode" v-model="selectedOrganizationState" aria-label="整理状态" class="article-state-filter">
              <ElOption label="全部整理状态" value="" />
              <ElOption label="待整理" value="inbox" />
              <ElOption label="已整理" value="organized" />
              <ElOption label="已归档" value="archived" />
            </ElSelect>
            <ElInput v-if="!isRecycleBinMode" v-model="searchText" clearable placeholder="搜索私人文章标题或正文" class="article-search" @keyup.enter="appliedSearch = searchText.trim()" @clear="appliedSearch = ''">
              <template #append><ElButton @click="appliedSearch = searchText.trim()">搜索</ElButton></template>
            </ElInput>
          </div>
          <ContentTabs
            v-model="selectedCategoryId"
            class="article-tabs"
            :items="categoryFilterOptions"
            aria-label="文章分类"
          />

          <div v-if="isTableViewMode" class="article-table-wrapper">
            <ElTable :data="articles" stripe class="article-table" empty-text="暂无文章">
              <ElTableColumn label="文章" :min-width="articleTableTitleMinWidth">
                <template #default="{ row }">
                  <div class="article-table-title-cell">
                    <div v-if="row.cover_url" class="article-table-cover">
                      <ArticleCoverImage :url="row.cover_url" :alt="row.title" />
                    </div>
                    <div class="article-table-title-meta">
                      <div class="article-table-title">{{ row.title }}</div>
                      <div class="article-table-excerpt">{{ row.excerpt || '暂无摘要' }}</div>
                      <div v-if="!isRecycleBinMode" class="article-derived">
                        <ElButton v-for="item in row.converted_items" :key="item.id" size="small" link @click="router.push(targetRoute(item.target_type, item.target_id))">{{ item.target_type === 'todo' ? '待办' : '资料' }}</ElButton>
                      </div>
                    </div>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="博客状态" :width="articleTableStatusWidth">
                <template #default="{ row }">
                  <ElTag :type="getStatusType(row.status)" size="small" effect="dark">
                    {{ row.status !== 'private' && row.has_unpublished_changes ? '待更新发布' : getStatusLabel(row.status) }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn v-if="!isRecycleBinMode && !isMobileViewport" label="整理状态" width="100">
                <template #default="{ row }">{{ row.organization_state === 'inbox' ? '待整理' : row.organization_state === 'archived' ? '已归档' : '已整理' }}</template>
              </ElTableColumn>
              <ElTableColumn v-if="!isMobileViewport" label="分类 / 标签" min-width="220">
                <template #default="{ row }">
                  <ElSpace wrap size="small">
                    <ElTag v-if="row.category" size="small" type="info">{{ row.category.name }}</ElTag>
                    <ElTag v-for="tag in row.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                    <span v-if="!row.category && row.tags.length === 0" class="article-table-placeholder">-</span>
                  </ElSpace>
                </template>
              </ElTableColumn>
              <ElTableColumn v-if="!isMobileViewport" label="字数" width="120">
                <template #default="{ row }">
                  {{ formatArticleWordCount(row.word_count) }}
                </template>
              </ElTableColumn>
              <ElTableColumn v-if="!isMobileViewport" label="创建时间" width="120">
                <template #default="{ row }">
                  {{ getArticlePublishDate(row as ArticleRecord) }}
                </template>
              </ElTableColumn>
              <ElTableColumn v-if="!isMobileViewport" label="最近编辑" width="170">
                <template #default="{ row }">
                  {{ getArticleEditDate(row as ArticleRecord) }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="操作" :width="articleTableActionWidth" fixed="right">
                <template #default="{ row }">
                  <ElSpace size="small">
                    <ElButton size="small" link type="primary" @click="router.push(resolve文章路径('/articles/edit', row.id))">
                      编辑
                    </ElButton>
                    <ElDropdown v-if="!isRecycleBinMode" trigger="click" @command="(action: string) => handleArticleAction(row, action)">
                      <ElButton size="small" link>更多</ElButton>
                      <template #dropdown>
                        <ElDropdownMenu>
                          <ElDropdownItem command="inbox">待整理</ElDropdownItem>
                          <ElDropdownItem command="organized">已整理</ElDropdownItem>
                          <ElDropdownItem command="archived">归档</ElDropdownItem>
                          <ElDropdownItem command="todo">转待办</ElDropdownItem>
                          <ElDropdownItem command="material">转资料</ElDropdownItem>
                        </ElDropdownMenu>
                      </template>
                    </ElDropdown>
                    <ElPopconfirm
                      :title="`确定将文章《${row.title || '未命名'}》移入回收站？`"
                      confirm-button-text="确定"
                      cancel-button-text="取消"
                      @confirm="deleteArticle(row.id)"
                    >
                      <template #reference><ElButton size="small" link type="danger">删除</ElButton></template>
                    </ElPopconfirm>
                  </ElSpace>
                </template>
              </ElTableColumn>
            </ElTable>
          </div>

          <template v-else>
            <ElCard v-for="article in articles" :key="article.id" shadow="hover" class="article-card">
              <div class="article-card-inner">
                <div v-if="article.cover_url" class="article-cover">
                  <ArticleCoverImage :url="article.cover_url" :alt="article.title" />
                </div>

                <div class="article-body">
                  <div class="article-header">
                    <h3 class="article-title">{{ article.title }}</h3>
                    <ElTag :type="getStatusType(article.status)" size="small" effect="dark" class="article-status-tag">
                      {{ article.status !== 'private' && article.has_unpublished_changes ? '待更新发布' : getStatusLabel(article.status) }}
                    </ElTag>
                  </div>
                  <p class="article-excerpt">{{ article.excerpt || '暂无摘要' }}</p>
                  <div v-if="!isRecycleBinMode" class="article-derived">
                    <ElTag size="small" type="info">{{ article.organization_state === 'inbox' ? '待整理' : article.organization_state === 'archived' ? '已归档' : '已整理' }}</ElTag>
                    <ElButton v-for="item in article.converted_items" :key="item.id" size="small" link @click="router.push(targetRoute(item.target_type, item.target_id))">{{ item.target_type === 'todo' ? '待办' : '资料' }}</ElButton>
                  </div>
                  <div class="article-meta">
                    <div class="article-meta-main">
                      <ElSpace size="small">
                        <ElTag v-if="article.category" size="small" type="info">{{ article.category.name }}</ElTag>
                        <ElTag v-for="tag in article.tags" :key="tag.id" size="small">{{ tag.name }}</ElTag>
                      </ElSpace>
                      <span class="article-meta-text">
                        <span>{{ getArticlePublishDate(article) }}</span>
                        <span>·</span>
                        <span>{{ formatArticleWordCount(article.word_count) }}</span>
                      </span>
                    </div>
                    <div class="article-actions">
                      <ElSpace size="small">
                        <template v-if="!isRecycleBinMode">
                          <ElButton size="small" @click="router.push(resolve文章路径('/articles/edit', article.id))">编辑</ElButton>
                          <ElSelect :model-value="article.organization_state" aria-label="整理状态" style="width: 94px" @change="(value: ArticleOrganizationState) => changeOrganizationState(article, value)">
                            <ElOption label="待整理" value="inbox" /><ElOption label="已整理" value="organized" /><ElOption label="已归档" value="archived" />
                          </ElSelect>
                          <ElButton size="small" @click="openConvertDialog(article, 'todo')">转待办</ElButton>
                          <ElButton size="small" @click="openConvertDialog(article, 'material')">转资料</ElButton>
                          <ElPopconfirm
                            :title="`确定将文章《${article.title || '未命名'}》移入回收站？`"
                            confirm-button-text="确定"
                            cancel-button-text="取消"
                            @confirm="deleteArticle(article.id)"
                          >
                            <template #reference><ElButton size="small" type="danger" text>删除</ElButton></template>
                          </ElPopconfirm>
                        </template>
                        <template v-else>
                          <ElButton size="small" @click="restoreArticle(article.id)">恢复</ElButton>
                          <ElPopconfirm
                            :title="`确定永久删除文章《${article.title || '未命名'}》？对应图片也会一并清理。`"
                            confirm-button-text="确定"
                            cancel-button-text="取消"
                            @confirm="deleteArticle(article.id)"
                          >
                            <template #reference><ElButton size="small" type="danger" text>彻底删除</ElButton></template>
                          </ElPopconfirm>
                        </template>
                      </ElSpace>
                    </div>
                  </div>
                </div>
              </div>
            </ElCard>
          </template>

          <ElEmpty v-if="isArticleListEmpty && !isTableViewMode" :description="emptyDescription" />

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
    </PageSectionShell>

    <BaseDialog v-model="showConvertDialog" :title="convertTarget === 'todo' ? '生成待办' : '生成资料'" width="520px" style="max-width: 94vw">
      <div class="article-convert-form">
        <ElInput v-model="convertTitle" maxlength="300" placeholder="标题" />
        <ElSelect v-if="convertTarget === 'material'" v-model="convertMaterialType" aria-label="资料类型"><ElOption label="文本" value="text" /><ElOption label="链接" value="link" /></ElSelect>
        <ElInput v-model="convertContent" type="textarea" :rows="8" :placeholder="convertTarget === 'material' && convertMaterialType === 'link' ? '链接地址' : '内容'" />
        <ElInput v-if="convertTarget === 'material'" v-model="convertNote" type="textarea" :rows="2" placeholder="备注" />
        <div class="article-convert-actions">
          <ElButton @click="showConvertDialog = false">取消</ElButton>
          <ElButton type="primary" :loading="converting" @click="submitConversion">创建</ElButton>
        </div>
      </div>
    </BaseDialog>

    <BaseDialog
      v-model="showTransferDialog"
      title="文章备份"
      width="460px"
      style="max-width: 90vw"
    >
      <div class="article-transfer-dialog">
        <div class="article-transfer-tip">
          长按“写文章”可打开此弹窗。系统会自动拉取当前账号下的全部文章详情，并导出为 JSON 文件，包含正文、摘要、封面、可见性、分类、标签与时间信息。
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
@import '@personal-system/ui/styles/media.css';

.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.page-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
}

.create-button-wrapper {
  display: flex;
  flex: 0 0 auto;
}

.article-mode-nav {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.article-mode-nav__item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-width: 68px;
  height: 30px;
  padding: 0 9px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--el-text-color-regular);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  line-height: 1;
  transition: background-color 0.15s, color 0.15s, box-shadow 0.15s;
  white-space: nowrap;
}

.article-mode-nav__item:hover {
  color: var(--el-color-primary);
}

.article-mode-nav__item.is-active {
  background: var(--el-bg-color);
  color: var(--el-color-primary);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
}

.article-card {
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-quick-entry,
.article-filters,
.article-derived,
.article-convert-form {
  display: flex;
  gap: 8px;
}

.article-quick-entry { align-items: flex-end; }
.article-quick-entry .el-textarea { flex: 1; }
.article-filters { align-items: center; }
.article-state-filter { width: 160px; flex: none; }
.article-search { max-width: 420px; }
.article-derived { align-items: center; margin-bottom: 10px; }
.article-convert-form { flex-direction: column; }
.article-convert-actions { display: flex; justify-content: flex-end; }

.article-tabs {
  margin-bottom: 4px;
}

.article-table-wrapper {
  width: 100%;
}

.article-table {
  width: 100%;
}

.article-table-title-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.article-table-cover {
  width: 72px;
  height: 48px;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 6px;
  background: var(--el-fill-color-light);
}

.article-table-cover :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.article-table-title-meta {
  min-width: 0;
}

.article-table-title {
  overflow: hidden;
  color: var(--el-text-color-primary);
  font-weight: 600;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-table-excerpt {
  display: -webkit-box;
  overflow: hidden;
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.5;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.article-table-placeholder {
  color: var(--el-text-color-placeholder);
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
  .article-quick-entry { align-items: stretch; flex-direction: column; }
  .article-filters { flex-wrap: wrap; }
  .article-search { max-width: none; width: 100%; }
  .page-container {
    padding: 16px;
  }

  .page-container :deep(.page-header-shell__header) {
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions {
    justify-content: stretch;
    flex-wrap: wrap;
  }

  .article-mode-nav {
    width: 100%;
  }

  .article-mode-nav__item {
    flex: 1 1 0;
    min-width: 0;
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

  .article-table-wrapper {
    max-width: 100%;
    overflow-x: hidden;
  }

  .article-table-title-cell {
    gap: 8px;
  }

  .article-table-cover {
    width: 48px;
    height: 36px;
  }

  .article-table-title {
    font-size: 13px;
  }

  .article-table-excerpt {
    display: none;
  }

  .article-table :deep(.el-table__cell) {
    padding: 8px 0;
  }

  .article-table :deep(.el-button) {
    padding: 0 4px;
  }
}
</style>
