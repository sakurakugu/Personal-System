<script setup lang="ts">
/* global Event, HTMLInputElement, IntersectionObserver, MouseEvent, TouchEvent */
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ElButton,
  ElCard,
  ElCheckbox,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElPopover,
  ElSelect,
  ElSpace,
  ElTag,
} from 'element-plus'
import { ArrowLeft, Collection, Delete, Filter, List, RefreshRight, Search, Select, Upload, WarningFilled } from '@element-plus/icons-vue'
import { BaseDialog, TagInlineInput, useLongPressSelection } from '@personal-system/ui'
import { getApiErrorMessage } from '@personal-system/api'
import FolderPickerDialog from '../components/FolderPickerDialog.vue'
import {
  batchUpdateCollectionStatus,
  convertCollectionToArticle,
  convertCollectionToMomentDraft,
  convertCollectionToTodo,
  createCollection,
  deleteCollection,
  fetchCollectionTags,
  fetchCollections,
  restoreCollection,
  updateCollection,
} from '../api'
import type {
  CollectionAssetPayload,
  CollectionAssetRecord,
  CollectionListQuery,
  CollectionListResponse,
  CollectionPayload,
  CollectionRecord,
  CollectionStatus,
  CollectionTagStat,
  CollectionType,
} from '../types'
import { createFolder, fetchExplorer, uploadFile } from '../files-api'
import type { FileTreeNode } from '../files-types'

interface CollectionFormState {
  type: CollectionType
  title: string
  content_text: string
  note: string
  status: CollectionStatus
  tags_text: string
  assets: Array<{
    file_id: string
    sort_order: number
    file: CollectionAssetRecord['file']
  }>
}

interface SwipeState {
  offset: number
  startX: number
  startY: number
  isDragging: boolean
  hasMoved: boolean
}

const route = useRoute()
const router = useRouter()
const pageContainerRef = ref<globalThis.HTMLDivElement | null>(null)
const loadMoreTriggerRef = ref<globalThis.HTMLDivElement | null>(null)
const uploadInputRef = ref<HTMLInputElement | null>(null)
const initialLoading = ref(true)
const refreshing = ref(false)
const loadingMore = ref(false)
const dialogLoading = ref(false)
const uploadLoading = ref(false)
const showDialog = ref(false)
const showFolderPickerDialog = ref(false)
const isEdit = ref(false)
const isMultiSelectMode = ref(false)
const showRecycleBin = ref(false)
const currentId = ref('')
const collections = ref<CollectionRecord[]>([])
const tagOptions = ref<CollectionTagStat[]>([])
const multiSelectedIds = ref<string[]>([])
const swipeState = reactive<Record<string, SwipeState>>({})
const COLLECTION_LIST_PAGE_SIZE = 12
const SWIPE_THRESHOLD = 86
const MAX_OFFSET = 122
const 收藏附件目录名 = '收藏附件'
const pagination = ref({ page: 0, pageSize: COLLECTION_LIST_PAGE_SIZE, total: 0, pageCount: 0 })
const filters = ref({
  keyword: '',
  status: '' as CollectionStatus | '',
  type: '' as CollectionType | '',
  tag: '',
})
const 选中的上传目录 = ref<string | null>(null)
const 选中的上传目录路径 = ref('全部文件')
let loadMoreObserver: IntersectionObserver | null = null
const 路由前缀 = computed(() => route.path.startsWith('/dashboard') ? '/dashboard' : '')

const { startLongPress, cancelLongPress, consumeLongPress } = useLongPressSelection<CollectionRecord>({
  getId: record => record.id,
  onLongPress: (record) => {
    enterMultiSelect(record)
  },
})

function createEmptyForm(): CollectionFormState {
  return {
    type: 'link',
    title: '',
    content_text: '',
    note: '',
    status: 'inbox',
    tags_text: '',
    assets: [],
  }
}

const form = ref<CollectionFormState>(createEmptyForm())

const typeOptions: Array<{ label: string, value: CollectionType }> = [
  { label: '网页链接', value: 'link' },
  { label: '文本', value: 'text' },
  { label: '图片', value: 'image' },
  { label: '文件', value: 'file' },
]
const statusOptions: Array<{ label: string, value: CollectionStatus }> = [
  { label: '刚收纳', value: 'inbox' },
  { label: '整理中', value: 'processing' },
  { label: '已就绪', value: 'ready' },
  { label: '已归档', value: 'archived' },
  { label: '已废弃', value: 'dropped' },
]
const hasSearchKeyword = computed(() => Boolean(filters.value.keyword.trim()))
const activeFilterCount = computed(() => [
  filters.value.type,
  filters.value.tag.trim(),
].filter(Boolean).length)
const hasAnyFilters = computed(() => hasSearchKeyword.value || Boolean(filters.value.status) || activeFilterCount.value > 0)
const isAssetType = computed(() => form.value.type === 'image' || form.value.type === 'file')
const hasCoreContent = computed(() => Boolean(
  form.value.title.trim()
  || form.value.content_text.trim()
  || form.value.note.trim(),
))
const shouldShowAnyContentRequiredMark = computed(() => !isAssetType.value && !hasCoreContent.value && form.value.assets.length === 0)
const shouldShowAssetRequiredMark = computed(() => isAssetType.value || (!hasCoreContent.value && form.value.assets.length === 0))
const allExistingTags = computed(() => tagOptions.value.map(item => item.name))
const availableTags = computed(() => getAvailableTags(form.value.tags_text))
const pageTitleText = computed(() => showRecycleBin.value ? '收藏回收站' : '收藏收纳库')
const statusButtonText = computed(() => filters.value.status ? getStatusLabel(filters.value.status) : '全部状态')
const hasMoreCollections = computed(() => pagination.value.page < pagination.value.pageCount)
const 当前上传目录标签 = computed(() => 选中的上传目录路径.value || '全部文件')
const selectedCollectionIdSet = computed(() => new Set(multiSelectedIds.value))
const visibleCollectionIdSet = computed(() => new Set(collections.value.map(record => record.id)))
const allVisibleSelected = computed(() => (
  collections.value.length > 0 && collections.value.every(record => selectedCollectionIdSet.value.has(record.id))
))
const hasSelectedCollectionNeedingArchive = computed(() => (
  collections.value.some(record => selectedCollectionIdSet.value.has(record.id) && record.status !== 'archived')
))
const showDeleteConfirm = ref(false)
const pendingDeleteIds = ref<string[]>([])
const deleteMode = ref<'soft' | 'permanent'>('soft')
const dontAskAgain = ref(false)
const DELETE_CONFIRM_KEY = 'collections_delete_confirm_dont_ask'
let deleteConfirmResolver: ((value: boolean) => void) | null = null

function parseTagsInput(tagsText: string): string[] {
  return tagsText
    .replaceAll('，', ',')
    .split(',')
    .map(tag => tag.trim())
    .filter(Boolean)
}

function parseTagsText(tagsText: string): string[] | null {
  const tags = parseTagsInput(tagsText)
  return tags.length > 0 ? Array.from(new Set(tags)) : null
}

function getAvailableTags(currentTagsStr: string): string[] {
  const currentTags = new Set(parseTagsInput(currentTagsStr))
  return allExistingTags.value.filter(tag => !currentTags.has(tag))
}

function addTagToForm(formTags: string, tag: string): string {
  const tags = parseTagsInput(formTags)
  if (!tags.includes(tag)) {
    tags.push(tag)
  }
  return tags.join(',')
}

function shouldSkipDeleteConfirm(): boolean {
  try {
    return globalThis.sessionStorage?.getItem(DELETE_CONFIRM_KEY) === 'true'
  } catch {
    return false
  }
}

function setDontAskAgain(value: boolean) {
  try {
    if (value) {
      globalThis.sessionStorage?.setItem(DELETE_CONFIRM_KEY, 'true')
    } else {
      globalThis.sessionStorage?.removeItem(DELETE_CONFIRM_KEY)
    }
  } catch {
    // ignore
  }
}

async function requestDeleteConfirm(ids: string[], mode: 'soft' | 'permanent'): Promise<boolean> {
  if (ids.length === 0) return false
  if (shouldSkipDeleteConfirm()) return true

  pendingDeleteIds.value = [...ids]
  deleteMode.value = mode
  dontAskAgain.value = false
  showDeleteConfirm.value = true

  return new Promise<boolean>((resolve) => {
    deleteConfirmResolver = resolve
  })
}

function cancelDeleteConfirm() {
  showDeleteConfirm.value = false
  pendingDeleteIds.value = []
  deleteMode.value = 'soft'
  dontAskAgain.value = false
  deleteConfirmResolver?.(false)
  deleteConfirmResolver = null
}

function confirmDeleteConfirm() {
  setDontAskAgain(dontAskAgain.value)
  showDeleteConfirm.value = false
  pendingDeleteIds.value = []
  deleteMode.value = 'soft'
  dontAskAgain.value = false
  deleteConfirmResolver?.(true)
  deleteConfirmResolver = null
}

function buildPayloadFromForm(): CollectionPayload {
  const assets: CollectionAssetPayload[] | null = form.value.assets.length > 0
    ? form.value.assets.map((asset, index) => ({
      file_id: asset.file_id,
      sort_order: index,
    }))
    : null

  return {
    type: form.value.type,
    title: form.value.title || null,
    content_text: form.value.content_text || null,
    note: form.value.note || null,
    status: form.value.status,
    tags: parseTagsText(form.value.tags_text),
    assets,
  }
}

function getTypeLabel(value: CollectionType | ''): string {
  return typeOptions.find(item => item.value === value)?.label ?? value
}

function getStatusLabel(value: CollectionStatus | ''): string {
  return statusOptions.find(item => item.value === value)?.label ?? value
}

function getStatusIcon(value: CollectionStatus | '') {
  if (value === 'processing') return RefreshRight
  if (value === 'ready') return Select
  if (value === 'archived') return Collection
  if (value === 'dropped') return WarningFilled
  return Upload
}

function getStatusTagType(value: CollectionStatus): 'info' | 'warning' | 'success' | 'danger' {
  if (value === 'ready') return 'success'
  if (value === 'processing') return 'warning'
  if (value === 'dropped') return 'danger'
  return 'info'
}

function getDisplayTitle(record: CollectionRecord): string {
  return record.title?.trim() || '未命名收藏'
}

function getPreviewText(record: CollectionRecord): string {
  return record.note || record.content_text || '暂无内容'
}

function getArchiveActionLabel(record: CollectionRecord): string {
  return record.status === 'archived' ? '取消归档' : '归档'
}

function getArchiveActionIcon(record: CollectionRecord) {
  return record.status === 'archived' ? RefreshRight : Collection
}

function isArchivedCollection(record: CollectionRecord): boolean {
  return record.status === 'archived'
}

function getLeftSwipeActionLabel(record: CollectionRecord): string {
  if (showRecycleBin.value) {
    return '恢复'
  }
  return getArchiveActionLabel(record)
}

function getLeftSwipeActionIcon(record: CollectionRecord) {
  if (showRecycleBin.value) {
    return RefreshRight
  }
  return getArchiveActionIcon(record)
}

function getRightSwipeActionLabel(): string {
  return showRecycleBin.value ? '永久删除' : '删除'
}

function getEmptyDescription(): string {
  return showRecycleBin.value ? '回收站里还没有收藏' : '还没有收藏内容'
}

function 查找根级收藏附件目录(tree: FileTreeNode[]): FileTreeNode | null {
  return tree.find(node => node.parent_id === null && node.name === 收藏附件目录名) ?? null
}

async function 初始化默认上传目录() {
  try {
    let explorer = await fetchExplorer()
    let 默认目录 = 查找根级收藏附件目录(explorer.tree)

    if (默认目录 === null) {
      try {
        await createFolder(收藏附件目录名)
      } catch {
        // 忽略并重新读取，兼容并发创建
      }
      explorer = await fetchExplorer()
      默认目录 = 查找根级收藏附件目录(explorer.tree)
    }

    if (默认目录) {
      选中的上传目录.value = 默认目录.id
      选中的上传目录路径.value = '全部文件 / 收藏附件'
      return
    }

    选中的上传目录.value = null
    选中的上传目录路径.value = '全部文件'
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载默认上传目录失败'))
  }
}

function 打开目录选择弹窗() {
  showFolderPickerDialog.value = true
}

function 应用上传目录选择(payload: { folderId: string | null, path: string }) {
  选中的上传目录.value = payload.folderId
  选中的上传目录路径.value = payload.path || '全部文件'
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString()
}

function resolve工作区路径(path: '/articles/edit' | '/moments' | '/todos') {
  return `${路由前缀.value}${path}`
}

function buildCollectionQuery(page: number, pageSize: number): CollectionListQuery {
  return {
    page,
    page_size: pageSize,
    keyword: filters.value.keyword.trim() || undefined,
    status: filters.value.status,
    type: filters.value.type,
    tag: filters.value.tag.trim() || undefined,
    is_deleted: showRecycleBin.value,
  }
}

function applyCollectionPage(data: CollectionListResponse, append: boolean) {
  collections.value = append ? [...collections.value, ...data.items] : data.items
  pagination.value = {
    page: data.page,
    pageSize: data.page_size,
    total: data.total,
    pageCount: data.pages,
  }
}

function disconnectLoadMoreObserver() {
  if (loadMoreObserver) {
    loadMoreObserver.disconnect()
    loadMoreObserver = null
  }
}

function isSelected(recordId: string): boolean {
  return selectedCollectionIdSet.value.has(recordId)
}

function enterMultiSelect(record: CollectionRecord) {
  isMultiSelectMode.value = true
  if (!selectedCollectionIdSet.value.has(record.id)) {
    multiSelectedIds.value = [...multiSelectedIds.value, record.id]
  }
}

function toggleMultiSelect(record: CollectionRecord) {
  isMultiSelectMode.value = true
  if (selectedCollectionIdSet.value.has(record.id)) {
    multiSelectedIds.value = multiSelectedIds.value.filter(id => id !== record.id)
    return
  }
  multiSelectedIds.value = [...multiSelectedIds.value, record.id]
}

function exitMultiSelect() {
  isMultiSelectMode.value = false
  multiSelectedIds.value = []
}

function toggleSelectAllVisibleCollections() {
  if (allVisibleSelected.value) {
    multiSelectedIds.value = multiSelectedIds.value.filter(id => !visibleCollectionIdSet.value.has(id))
    return
  }
  multiSelectedIds.value = collections.value.map(record => record.id)
}

function initSwipeState(id: string) {
  if (!swipeState[id]) {
    swipeState[id] = {
      offset: 0,
      startX: 0,
      startY: 0,
      isDragging: false,
      hasMoved: false,
    }
  }
}

function onTouchStart(event: Event, id: string) {
  if (isMultiSelectMode.value) return
  initSwipeState(id)
  const state = swipeState[id]
  state.isDragging = true

  if (event instanceof TouchEvent) {
    state.startX = event.touches[0].clientX
    state.startY = event.touches[0].clientY
  } else if (event instanceof MouseEvent) {
    state.startX = event.clientX
    state.startY = event.clientY
  }
}

function onTouchMove(event: Event, id: string) {
  if (isMultiSelectMode.value) return
  const state = swipeState[id]
  if (!state?.isDragging) return

  let clientX = 0
  let clientY = 0
  if (event instanceof TouchEvent) {
    clientX = event.touches[0].clientX
    clientY = event.touches[0].clientY
  } else if (event instanceof MouseEvent) {
    clientX = event.clientX
    clientY = event.clientY
  }

  const deltaX = clientX - state.startX
  const deltaY = clientY - state.startY

  if (Math.abs(deltaX) > 6 || Math.abs(deltaY) > 6) {
    cancelLongPressById(id)
  }

  if (Math.abs(deltaY) > Math.abs(deltaX)) {
    return
  }

  if (Math.abs(deltaX) > 6) {
    state.hasMoved = true
    cancelLongPressById(id)
  }

  if (event instanceof TouchEvent && Math.abs(deltaX) > 10) {
    event.preventDefault()
  }

  state.offset = Math.max(-MAX_OFFSET, Math.min(MAX_OFFSET, deltaX))
}

function cancelLongPressById(id: string) {
  const record = collections.value.find(item => item.id === id)
  if (record) {
    cancelLongPress(record)
  }
}

function resetSwipeState(id: string) {
  const state = swipeState[id]
  if (!state) return
  state.offset = 0
  state.isDragging = false
  state.hasMoved = false
}

async function onTouchEnd(record: CollectionRecord) {
  if (isMultiSelectMode.value) return
  const state = swipeState[record.id]
  if (!state) return

  const offset = state.offset
  const hadMoved = state.hasMoved
  state.isDragging = false

  if (hadMoved) {
    setTimeout(() => {
      if (swipeState[record.id]) {
        swipeState[record.id].hasMoved = false
      }
    }, 50)
  } else {
    state.hasMoved = false
  }

  state.offset = 0

  if (offset <= -SWIPE_THRESHOLD) {
    await removeCollection(record.id)
    return
  }

  if (offset >= SWIPE_THRESHOLD) {
    await toggleArchiveCollection(record)
  }
}

function onTouchCancel(record: CollectionRecord) {
  cancelLongPress(record)
  resetSwipeState(record.id)
}

function getCardStyle(id: string) {
  const state = swipeState[id]
  if (!state) return {}
  return {
    transform: `translateX(${state.offset}px)`,
    transition: state.isDragging ? 'none' : 'transform 0.26s ease',
  }
}

function getLeftActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }
  const progress = Math.min(1, Math.max(0, state.offset / SWIPE_THRESHOLD))
  return {
    opacity: progress,
    transform: `translateX(${(-16 + progress * 16).toFixed(2)}px) scale(${(0.88 + progress * 0.12).toFixed(3)})`,
  }
}

function getRightActionStyle(id: string) {
  const state = swipeState[id]
  if (!state) return { opacity: 0 }
  const progress = Math.min(1, Math.max(0, -state.offset / SWIPE_THRESHOLD))
  return {
    opacity: progress,
    transform: `translateX(${(16 - progress * 16).toFixed(2)}px) scale(${(0.88 + progress * 0.12).toFixed(3)})`,
  }
}

async function requestCollectionPage(page: number, append: boolean) {
  const data = await fetchCollections(buildCollectionQuery(page, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE))
  applyCollectionPage(data, append)
}

async function 获取指定可见数量的收藏(targetVisibleCount: number) {
  const pageSize = pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE
  const firstPage = await fetchCollections(buildCollectionQuery(1, pageSize))
  const items = [...firstPage.items]
  let currentPage = firstPage.page

  while (items.length < targetVisibleCount && currentPage < firstPage.pages) {
    currentPage += 1
    const data = await fetchCollections(buildCollectionQuery(currentPage, pageSize))
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

async function reloadCollections(
  targetVisibleCount = pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE,
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
    const data = await 获取指定可见数量的收藏(targetVisibleCount)
    collections.value = data.items
    pagination.value = {
      page: data.page,
      pageSize: data.pageSize,
      total: data.total,
      pageCount: data.pageCount,
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载收藏失败'))
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      initialLoading.value = false
    }
  }
}

async function fetchNextPage() {
  if (initialLoading.value || refreshing.value || loadingMore.value || !hasMoreCollections.value) {
    return
  }
  loadingMore.value = true
  try {
    await requestCollectionPage(pagination.value.page + 1, true)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载更多收藏失败'))
  } finally {
    loadingMore.value = false
  }
}

async function loadTags() {
  try {
    tagOptions.value = await fetchCollectionTags(showRecycleBin.value)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载标签失败'))
  }
}

function applyFilters() {
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function resetAllFilters() {
  filters.value = {
    keyword: '',
    status: '',
    type: '',
    tag: '',
  }
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function clearKeywordFilter() {
  filters.value.keyword = ''
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function clearStatusFilter() {
  filters.value.status = ''
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function selectStatusFilter(status: CollectionStatus | '') {
  filters.value.status = status
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function clearTypeFilter() {
  filters.value.type = ''
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function clearTagFilter() {
  filters.value.tag = ''
  void reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true })
}

function openRecycleBin() {
  showRecycleBin.value = true
  exitMultiSelect()
  void Promise.all([
    reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true }),
    loadTags(),
  ])
}

function closeRecycleBin() {
  showRecycleBin.value = false
  exitMultiSelect()
  void Promise.all([
    reloadCollections(COLLECTION_LIST_PAGE_SIZE, { silent: true }),
    loadTags(),
  ])
}

function openCreateDialog() {
  if (showRecycleBin.value) {
    return
  }
  isEdit.value = false
  currentId.value = ''
  form.value = createEmptyForm()
  选中的上传目录.value = null
  选中的上传目录路径.value = '全部文件'
  exitMultiSelect()
  showDialog.value = true
}

function openEditDialog(record: CollectionRecord) {
  if (showRecycleBin.value) {
    return
  }
  isEdit.value = true
  currentId.value = record.id
  exitMultiSelect()
  form.value = {
    type: record.type,
    title: record.title || '',
    content_text: record.content_text || '',
    note: record.note || '',
    status: record.status,
    tags_text: (record.tags || []).join(', '),
    assets: record.assets.map(asset => ({
      file_id: asset.file_id,
      sort_order: asset.sort_order,
      file: asset.file,
    })),
  }
  选中的上传目录.value = null
  选中的上传目录路径.value = '全部文件'
  showDialog.value = true
}

function validateCollectionForm(): boolean {
  if (isAssetType.value && form.value.assets.length === 0) {
    ElMessage.error(`"${getTypeLabel(form.value.type)}"类型至少需要上传一个附件`)
    return false
  }
  if (!hasCoreContent.value && form.value.assets.length === 0) {
    ElMessage.error('标题、正文提取、备注或附件至少填写一项')
    return false
  }
  return true
}

async function saveCollection(keepDialogOpen = false) {
  if (!validateCollectionForm()) {
    return
  }
  dialogLoading.value = true
  try {
    const payload = buildPayloadFromForm()
    const targetVisibleCount = Math.max(
      collections.value.length + (isEdit.value ? 0 : 1),
      pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE,
    )
    if (isEdit.value) {
      await updateCollection(currentId.value, payload)
      ElMessage.success('收藏已更新')
      showDialog.value = false
    } else {
      await createCollection(payload)
      ElMessage.success(keepDialogOpen ? '收藏已创建，可继续录入' : '收藏已创建')
      if (keepDialogOpen) {
        form.value = createEmptyForm()
      } else {
        showDialog.value = false
      }
    }
    await Promise.all([reloadCollections(targetVisibleCount, { silent: true }), loadTags()])
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存收藏失败'))
  } finally {
    dialogLoading.value = false
  }
}

async function removeCollection(id: string) {
  const mode = showRecycleBin.value ? 'permanent' : 'soft'
  const confirmed = await requestDeleteConfirm([id], mode)
  if (!confirmed) {
    return
  }

  try {
    await deleteCollection(id, showRecycleBin.value)
    ElMessage.success(showRecycleBin.value ? '收藏已永久删除' : '收藏已移至回收站')
    const targetVisibleCount = Math.max(collections.value.length - 1, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE)
    await Promise.all([reloadCollections(targetVisibleCount, { silent: true }), loadTags()])
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, showRecycleBin.value ? '永久删除收藏失败' : '删除收藏失败'))
  }
}

async function toggleArchiveCollection(record: CollectionRecord) {
  if (showRecycleBin.value) {
    try {
      await restoreCollection(record.id)
      ElMessage.success('收藏已恢复')
      await Promise.all([
        reloadCollections(Math.max(collections.value.length - 1, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE), { silent: true }),
        loadTags(),
      ])
    } catch (error) {
      ElMessage.error(getApiErrorMessage(error, '恢复收藏失败'))
    }
    return
  }

  const nextStatus: CollectionStatus = record.status === 'archived' ? 'inbox' : 'archived'
  const successText = record.status === 'archived' ? '已取消归档' : '已归档'
  try {
    await updateCollection(record.id, { status: nextStatus })
    ElMessage.success(successText)
    await reloadCollections(Math.max(collections.value.length, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE), { silent: true })
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, `${getArchiveActionLabel(record)}失败`))
  }
}

async function batchToggleArchiveSelectedCollections() {
  if (showRecycleBin.value) {
    const targetIds = collections.value
      .filter(record => selectedCollectionIdSet.value.has(record.id))
      .map(record => record.id)

    if (targetIds.length === 0) {
      exitMultiSelect()
      return
    }

    try {
      await Promise.all(targetIds.map(id => restoreCollection(id)))
      ElMessage.success(`已恢复 ${targetIds.length} 条收藏`)
      exitMultiSelect()
      await Promise.all([
        reloadCollections(Math.max(collections.value.length - targetIds.length, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE), { silent: true }),
        loadTags(),
      ])
    } catch (error) {
      ElMessage.error(getApiErrorMessage(error, '批量恢复失败'))
    }
    return
  }

  const targetStatus: CollectionStatus = hasSelectedCollectionNeedingArchive.value ? 'archived' : 'inbox'
  const targetIds = collections.value
    .filter(record => selectedCollectionIdSet.value.has(record.id) && record.status !== targetStatus)
    .map(record => record.id)

  if (targetIds.length === 0) {
    exitMultiSelect()
    return
  }

  try {
    const count = await batchUpdateCollectionStatus({ ids: targetIds, status: targetStatus })
    ElMessage.success(targetStatus === 'archived' ? `已归档 ${count} 条收藏` : `已取消归档 ${count} 条收藏`)
    exitMultiSelect()
    await reloadCollections(Math.max(collections.value.length, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE), { silent: true })
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, targetStatus === 'archived' ? '批量归档失败' : '批量取消归档失败'))
  }
}

async function batchDeleteSelectedCollections() {
  const targetIds = collections.value
    .filter(record => selectedCollectionIdSet.value.has(record.id))
    .map(record => record.id)

  if (targetIds.length === 0) {
    exitMultiSelect()
    return
  }

  const mode = showRecycleBin.value ? 'permanent' : 'soft'
  const confirmed = await requestDeleteConfirm(targetIds, mode)
  if (!confirmed) {
    return
  }

  try {
    await Promise.all(targetIds.map(id => deleteCollection(id, showRecycleBin.value)))
    ElMessage.success(showRecycleBin.value ? `已永久删除 ${targetIds.length} 条收藏` : `已移至回收站 ${targetIds.length} 条收藏`)
    exitMultiSelect()
    const targetVisibleCount = Math.max(collections.value.length - targetIds.length, pagination.value.pageSize || COLLECTION_LIST_PAGE_SIZE)
    await Promise.all([reloadCollections(targetVisibleCount, { silent: true }), loadTags()])
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, showRecycleBin.value ? '批量永久删除失败' : '批量删除失败'))
  }
}

async function handleConvertToArticle(record: CollectionRecord) {
  try {
    const result = await convertCollectionToArticle(record.id)
    ElMessage.success(result.message)
    await router.push(`${resolve工作区路径('/articles/edit')}/${result.target_id}`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '转文章失败'))
  }
}

async function handleConvertToMoment(record: CollectionRecord) {
  try {
    const result = await convertCollectionToMomentDraft(record.id)
    ElMessage.success(result.message)
    await router.push(resolve工作区路径('/moments'))
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '转动态草稿失败'))
  }
}

async function handleConvertToTodo(record: CollectionRecord) {
  try {
    const result = await convertCollectionToTodo(record.id)
    ElMessage.success(result.message)
    await router.push(resolve工作区路径('/todos'))
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '转待办失败'))
  }
}

async function openUploadPicker() {
  uploadInputRef.value?.click()
}

async function handleUploadChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) {
    return
  }

  uploadLoading.value = true
  try {
    const folderId = 选中的上传目录.value
    for (const file of files) {
      const uploaded = await uploadFile(file, folderId)
      form.value.assets.push({
        file_id: uploaded.id,
        sort_order: form.value.assets.length,
        file: uploaded,
      })
    }
    ElMessage.success(`已上传 ${files.length} 个附件`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '上传附件失败'))
  } finally {
    uploadLoading.value = false
    input.value = ''
  }
}

function removeAsset(index: number) {
  form.value.assets.splice(index, 1)
}

function moveAsset(index: number, direction: -1 | 1) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= form.value.assets.length) {
    return
  }
  const [item] = form.value.assets.splice(index, 1)
  form.value.assets.splice(targetIndex, 0, item)
}

function handleCardClick(record: CollectionRecord) {
  if (consumeLongPress(record)) {
    return
  }
  const state = swipeState[record.id]
  if (state?.hasMoved) {
    return
  }
  if (isMultiSelectMode.value) {
    toggleMultiSelect(record)
    return
  }
  if (showRecycleBin.value) {
    return
  }
  openEditDialog(record)
}

onMounted(async () => {
  await Promise.all([reloadCollections(COLLECTION_LIST_PAGE_SIZE), loadTags()])
})

onBeforeUnmount(() => {
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
        if (!entries.some(entry => entry.isIntersecting)) {
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

watch(collections, (items) => {
  const idSet = new Set(items.map(item => item.id))
  multiSelectedIds.value = multiSelectedIds.value.filter(id => idSet.has(id))
  if (isMultiSelectMode.value && multiSelectedIds.value.length === 0) {
    isMultiSelectMode.value = false
  }
})

watch(showDeleteConfirm, (value) => {
  if (!value && deleteConfirmResolver) {
    pendingDeleteIds.value = []
    deleteMode.value = 'soft'
    dontAskAgain.value = false
    deleteConfirmResolver(false)
    deleteConfirmResolver = null
  }
})

watch(showDialog, (visible) => {
  if (!visible) {
    showFolderPickerDialog.value = false
    return
  }
  void 初始化默认上传目录()
})
</script>

<template>
  <div ref="pageContainerRef" class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <ElIcon><Collection /></ElIcon>
        <span>{{ pageTitleText }}</span>
      </h2>
      <ElSpace wrap>
        <ElButton v-if="showRecycleBin" @click="closeRecycleBin">
          <ElIcon><ArrowLeft /></ElIcon>
          <span>返回列表</span>
        </ElButton>
        <ElButton v-else @click="openRecycleBin">
          <ElIcon><Delete /></ElIcon>
          <span>回收站</span>
        </ElButton>
        <ElButton v-if="!showRecycleBin" type="primary" @click="openCreateDialog">+ 新增收藏</ElButton>
      </ElSpace>
    </div>

    <div class="status-bar">
      <div class="status-bar-left">
        <div class="filter-tools">
          <ElInput
            v-model="filters.keyword"
            class="todo-search-input"
            clearable
            placeholder="搜索标题、正文、备注"
            @clear="applyFilters"
            @keyup.enter="applyFilters"
          >
            <template #prefix>
              <ElIcon><Search /></ElIcon>
            </template>
          </ElInput>

          <div class="filter-button-group">
            <ElPopover trigger="click" :width="180" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
              <template #reference>
                <ElButton>
                  <span style="display: flex; align-items: center; gap: 6px">
                    <ElIcon><List /></ElIcon>
                    <span>{{ statusButtonText }}</span>
                    <span style="margin-left: 4px">▼</span>
                  </span>
                </ElButton>
              </template>
              <div class="status-filter-list">
                <div
                  class="status-filter-item"
                  :class="{ 'is-selected': !filters.status }"
                  @click="selectStatusFilter('')"
                >
                  <span class="status-filter-text">
                    <ElIcon><List /></ElIcon>
                    <span>全部状态</span>
                  </span>
                </div>
                <div
                  v-for="item in statusOptions"
                  :key="item.value"
                  class="status-filter-item"
                  :class="{ 'is-selected': filters.status === item.value }"
                  @click="selectStatusFilter(item.value)"
                >
                  <span class="status-filter-text">
                    <ElIcon><component :is="getStatusIcon(item.value)" /></ElIcon>
                    <span>{{ item.label }}</span>
                  </span>
                </div>
                <div class="status-filter-divider" />
                <template v-if="!showRecycleBin">
                  <div class="status-filter-item" @click="openRecycleBin">
                    <span class="status-filter-text">
                      <ElIcon><Delete /></ElIcon>
                      <span>回收站</span>
                    </span>
                  </div>
                </template>
                <template v-else>
                  <div class="status-filter-item" @click="closeRecycleBin">
                    <span class="status-filter-text">
                      <ElIcon><ArrowLeft /></ElIcon>
                      <span>返回列表</span>
                    </span>
                  </div>
                </template>
              </div>
            </ElPopover>

            <ElPopover trigger="click" :width="280" :show-arrow="false" popper-class="status-filter-popover" :offset="8">
              <template #reference>
                <ElButton>
                  <span style="display: flex; align-items: center; gap: 6px">
                    <ElIcon><Filter /></ElIcon>
                    <span>{{ activeFilterCount > 0 ? `更多筛选(${activeFilterCount})` : '更多筛选' }}</span>
                    <span style="margin-left: 4px">▼</span>
                  </span>
                </ElButton>
              </template>
              <div class="advanced-filter-panel">
                <div class="advanced-filter-field">
                  <span class="advanced-filter-label">类型</span>
                  <ElSelect v-model="filters.type" clearable placeholder="全部类型" size="small">
                    <ElOption v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
                  </ElSelect>
                </div>

                <div class="advanced-filter-field">
                  <span class="advanced-filter-label">标签</span>
                  <ElSelect v-model="filters.tag" clearable filterable placeholder="全部标签" size="small">
                    <ElOption v-for="item in tagOptions" :key="item.name" :label="`${item.name} (${item.count})`" :value="item.name" />
                  </ElSelect>
                </div>

                <div class="advanced-filter-actions">
                  <ElButton link @click="resetAllFilters">重置筛选</ElButton>
                  <ElButton type="primary" size="small" @click="applyFilters">应用筛选</ElButton>
                </div>
              </div>
            </ElPopover>

            <ElButton type="primary" @click="applyFilters">搜索</ElButton>
          </div>
        </div>

        <div v-if="hasAnyFilters" class="active-filters">
          <ElTag v-if="hasSearchKeyword" closable @close="clearKeywordFilter">
            搜索：{{ filters.keyword.trim() }}
          </ElTag>
          <ElTag v-if="filters.status" closable @close="clearStatusFilter">
            状态：{{ getStatusLabel(filters.status) }}
          </ElTag>
          <ElTag v-if="filters.type" closable @close="clearTypeFilter">
            类型：{{ getTypeLabel(filters.type) }}
          </ElTag>
          <ElTag v-if="filters.tag.trim()" closable @close="clearTagFilter">
            标签：{{ filters.tag.trim() }}
          </ElTag>
          <ElButton link class="filter-reset-button" @click="resetAllFilters">清空全部</ElButton>
        </div>
      </div>
    </div>

    <div v-if="isMultiSelectMode" class="multi-select-toolbar">
      <div class="multi-select-toolbar__summary">
        <ElIcon><Select /></ElIcon>
        <span>已选择 {{ multiSelectedIds.length }} 项</span>
      </div>
      <div class="multi-select-toolbar__actions">
        <ElButton @click="toggleSelectAllVisibleCollections">
          {{ allVisibleSelected ? '取消全选' : '全选当前页' }}
        </ElButton>
        <ElButton @click="exitMultiSelect">退出多选</ElButton>
        <ElButton @click="batchToggleArchiveSelectedCollections">
          {{ showRecycleBin ? '批量恢复' : (hasSelectedCollectionNeedingArchive ? '批量归档' : '批量取消归档') }}
        </ElButton>
        <ElButton type="danger" @click="batchDeleteSelectedCollections">
          {{ showRecycleBin ? '批量永久删除' : '批量删除' }}
        </ElButton>
      </div>
    </div>

    <div v-loading="initialLoading || refreshing" class="collection-list-wrap">
      <div v-if="collections.length > 0" class="collection-list">
        <div
          v-for="record in collections"
          :key="record.id"
          class="collection-swipe-item"
          @touchstart.passive="(event: Event) => { startLongPress(record, event); onTouchStart(event, record.id) }"
          @touchmove="(event: Event) => onTouchMove(event, record.id)"
          @touchend="() => { cancelLongPress(record); void onTouchEnd(record) }"
          @touchcancel="() => onTouchCancel(record)"
          @mousedown="(event: Event) => { startLongPress(record, event); onTouchStart(event, record.id) }"
          @mousemove="(event: Event) => onTouchMove(event, record.id)"
          @mouseup="() => { cancelLongPress(record); void onTouchEnd(record) }"
          @mouseleave="() => onTouchCancel(record)"
        >
          <div class="swipe-action left-action" :style="getLeftActionStyle(record.id)">
            <ElIcon :size="22"><component :is="getLeftSwipeActionIcon(record)" /></ElIcon>
            <span class="action-text">{{ getLeftSwipeActionLabel(record) }}</span>
          </div>

          <div class="swipe-action right-action" :style="getRightActionStyle(record.id)">
            <ElIcon :size="22"><Delete /></ElIcon>
            <span class="action-text">{{ getRightSwipeActionLabel() }}</span>
          </div>

          <ElCard
            class="collection-card"
            :class="{
              'is-selected': isSelected(record.id),
              'is-multi-select': isMultiSelectMode,
              'is-archived': isArchivedCollection(record),
            }"
            :style="getCardStyle(record.id)"
            shadow="hover"
            @click="handleCardClick(record)"
          >
            <div v-if="isMultiSelectMode" class="select-indicator" :class="{ 'is-selected': isSelected(record.id) }">
              <ElIcon><Select /></ElIcon>
            </div>
            <div class="collection-card-layout">
              <div class="collection-card-main">
                <div class="collection-title-block">
                  <div class="collection-title">{{ getDisplayTitle(record) }}</div>
                </div>

                <div class="collection-preview">
                  {{ getPreviewText(record) }}
                </div>

                <div class="collection-meta-row">
                  <div class="collection-meta-content">
                    <div class="collection-meta-group">
                      <div class="collection-meta-line">
                        <ElTag size="small">{{ getTypeLabel(record.type) }}</ElTag>
                        <ElTag size="small" :type="getStatusTagType(record.status)">{{ getStatusLabel(record.status) }}</ElTag>
                      </div>
                    </div>
                    <span class="collection-meta-divider">|</span>
                    <div class="collection-meta-group collection-meta-group--secondary">
                      <div class="collection-meta-line">
                        <template v-if="record.tags?.length">
                          <ElTag v-for="tag in record.tags" :key="tag" size="small" type="info" effect="plain">
                            {{ tag }}
                          </ElTag>
                        </template>
                        <span v-else class="collection-meta-text">无标签</span>
                        <span class="collection-meta-text">附件 {{ record.assets.length }}</span>
                        <span v-if="record.archived_at && isArchivedCollection(record)" class="collection-meta-text">
                          归档于 {{ formatDateTime(record.archived_at) }}
                        </span>
                        <span class="collection-meta-text">更新于 {{ formatDateTime(record.updated_at) }}</span>
                      </div>
                    </div>
                  </div>

                  <div
                    v-if="!isMultiSelectMode && !showRecycleBin"
                    class="collection-card-actions"
                    @click.stop
                    @mousedown.stop
                    @touchstart.stop
                  >
                    <ElButton class="action-button" @click.stop="handleConvertToArticle(record)">转文章</ElButton>
                    <ElButton class="action-button" @click.stop="handleConvertToMoment(record)">转动态</ElButton>
                    <ElButton class="action-button" @click.stop="handleConvertToTodo(record)">转待办</ElButton>
                  </div>
                </div>
              </div>
            </div>
          </ElCard>
        </div>
      </div>

      <ElEmpty v-else-if="!initialLoading" :description="getEmptyDescription()" />

      <div
        v-if="collections.length > 0 && hasMoreCollections"
        ref="loadMoreTriggerRef"
        class="collection-load-trigger"
        aria-hidden="true"
      />
      <div v-if="loadingMore" class="collection-list-status">
        正在加载更早的收藏...
      </div>
      <div v-else-if="collections.length > 0 && !hasMoreCollections" class="collection-list-status collection-list-status--end">
        已显示全部收藏
      </div>
    </div>

    <BaseDialog
      v-model="showDeleteConfirm"
      title="确认删除"
      width="360px"
      style="max-width: 90vw"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="delete-confirm-content">
        <ElIcon :size="40" color="#f56c6c"><WarningFilled /></ElIcon>
        <span>
          {{
            deleteMode === 'permanent'
              ? (pendingDeleteIds.length > 1 ? `确定永久删除选中的 ${pendingDeleteIds.length} 条收藏吗？此操作不可恢复。` : '确定永久删除这条收藏吗？此操作不可恢复。')
              : (pendingDeleteIds.length > 1 ? `确定将选中的 ${pendingDeleteIds.length} 条收藏移至回收站吗？` : '确定将这条收藏移至回收站吗？')
          }}
        </span>
      </div>
      <div class="delete-confirm-checkbox">
        <ElCheckbox v-model="dontAskAgain">本次都不再询问（刷新后恢复）</ElCheckbox>
      </div>
      <template #footer>
        <div class="delete-confirm-actions">
          <ElButton @click="cancelDeleteConfirm">取消</ElButton>
          <ElButton type="danger" @click="confirmDeleteConfirm">
            {{ deleteMode === 'permanent' ? '永久删除' : '移至回收站' }}
          </ElButton>
        </div>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model="showDialog"
      :title="isEdit ? '编辑收藏' : '新增收藏'"
      width="760px"
      style="max-width: 96vw"
    >
      <ElForm label-position="top">
        <div class="dialog-grid">
          <ElFormItem label="类型">
            <ElSelect v-model="form.type">
              <ElOption v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="状态">
            <ElSelect v-model="form.status">
              <ElOption v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
        </div>

        <ElFormItem>
          <template #label>
            <span>标题<span v-if="shouldShowAnyContentRequiredMark" class="required-mark">*</span></span>
          </template>
          <ElInput v-model="form.title" placeholder="收藏标题，可留空" maxlength="300" />
        </ElFormItem>
        <ElFormItem>
          <template #label>
            <span>正文提取<span v-if="shouldShowAnyContentRequiredMark" class="required-mark">*</span></span>
          </template>
          <ElInput v-model="form.content_text" type="textarea" :rows="5" placeholder="网页正文或手动粘贴内容" />
        </ElFormItem>
        <ElFormItem>
          <template #label>
            <span>备注<span v-if="shouldShowAnyContentRequiredMark" class="required-mark">*</span></span>
          </template>
          <ElInput v-model="form.note" type="textarea" :rows="4" placeholder="补充备注、整理思路、后续动作" />
        </ElFormItem>
        <div v-if="shouldShowAnyContentRequiredMark" class="required-hint">
          标题、正文提取、备注或附件至少填写一项
        </div>
        <ElFormItem label="标签">
          <TagInlineInput v-model="form.tags_text" :existing-tags="allExistingTags" placeholder="标签，用逗号分隔" />
          <div v-if="availableTags.length > 0" class="existing-tags">
            <ElTag
              v-for="tag in availableTags"
              :key="tag"
              size="small"
              effect="plain"
              class="existing-tag"
              @click="form.tags_text = addTagToForm(form.tags_text, tag)"
            >
              {{ tag }}
            </ElTag>
          </div>
        </ElFormItem>

        <ElFormItem>
          <template #label>
            <span>附件<span v-if="shouldShowAssetRequiredMark" class="required-mark">*</span></span>
          </template>
          <div class="asset-panel">
            <div v-if="isAssetType" class="required-hint">
              {{ getTypeLabel(form.type) }}类型至少需要上传一个附件
            </div>
            <div class="asset-toolbar">
              <div class="asset-folder-summary">
                <button type="button" class="asset-folder-summary__path" @click="打开目录选择弹窗">
                  {{ 当前上传目录标签 }}
                </button>
              </div>
              <ElButton :loading="uploadLoading" @click="openUploadPicker">
                <ElIcon><Upload /></ElIcon>
                <span>上传附件</span>
              </ElButton>
              <input
                ref="uploadInputRef"
                class="hidden-upload"
                type="file"
                multiple
                @change="handleUploadChange"
              >
            </div>

            <div v-if="form.assets.length === 0" class="asset-empty">
              暂无附件
            </div>

            <div v-else class="asset-list">
              <div v-for="(asset, index) in form.assets" :key="asset.file_id" class="asset-item">
                <div class="asset-info">
                  <a :href="asset.file.url" target="_blank" class="asset-name">
                    {{ asset.file.original_name }}
                  </a>
                  <div class="asset-meta">
                    {{ asset.file.mime_type }} · {{ Math.max(1, Math.round(asset.file.size / 1024)) }} KB
                  </div>
                </div>
                <div class="asset-actions">
                  <ElButton text :disabled="index === 0" @click="moveAsset(index, -1)">上移</ElButton>
                  <ElButton text :disabled="index === form.assets.length - 1" @click="moveAsset(index, 1)">下移</ElButton>
                  <ElButton text type="danger" @click="removeAsset(index)">移除</ElButton>
                </div>
              </div>
            </div>
          </div>
        </ElFormItem>
      </ElForm>

      <template #footer>
        <div class="dialog-footer-actions">
          <template v-if="isEdit">
            <ElButton @click="showDialog = false">取消</ElButton>
            <ElButton type="primary" :loading="dialogLoading" @click="saveCollection()">
              保存修改
            </ElButton>
          </template>
          <template v-else>
            <ElButton :disabled="dialogLoading" @click="saveCollection(true)">再创</ElButton>
            <ElButton type="primary" :loading="dialogLoading" @click="saveCollection()">
              创建收藏
            </ElButton>
          </template>
        </div>
      </template>
    </BaseDialog>

    <FolderPickerDialog
      v-model="showFolderPickerDialog"
      title="选择上传目录"
      :initial-folder-id="选中的上传目录"
      @confirm="应用上传目录选择"
    />
  </div>
</template>

<style scoped>
@import '@personal-system/ui/styles/media.css';

.page-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px 24px 120px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.status-bar {
  margin-bottom: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-bar-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-button-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-button-group :deep(.el-button) {
  margin-left: 0;
}

.todo-search-input {
  width: min(320px, 100%);
  max-width: 320px;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filter-reset-button {
  padding: 0;
  height: auto;
}

.advanced-filter-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.advanced-filter-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.advanced-filter-label {
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.advanced-filter-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-filter-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.status-filter-item:hover {
  background-color: var(--el-fill-color-light);
}

.status-filter-item.is-selected {
  background-color: var(--el-fill-color);
}

.status-filter-text {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.status-filter-divider {
  height: 1px;
  margin: 6px 8px;
  background: var(--el-border-color-lighter);
}

.multi-select-toolbar {
  position: fixed;
  left: 50%;
  bottom: calc(24px + var(--app-safe-area-bottom));
  transform: translateX(-50%);
  z-index: 1200;
  width: min(920px, calc(100vw - 32px));
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.18);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.multi-select-toolbar__summary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.multi-select-toolbar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.collection-list-wrap {
  min-height: 360px;
}

.collection-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.collection-swipe-item {
  position: relative;
  touch-action: pan-y;
  user-select: none;
}

.swipe-action {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 110px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 18px;
  color: #fff;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.left-action {
  left: 0;
  background: linear-gradient(90deg, var(--el-color-success) 0%, var(--el-color-success-light-3) 100%);
}

.right-action {
  right: 0;
  background: linear-gradient(135deg, #f56c6c 0%, #fb8b8b 100%);
}

.action-text {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.collection-card {
  --collection-card-accent-color: #67c23a;
  --collection-card-surface-color: rgba(103, 194, 58, 0.12);
  position: relative;
  z-index: 1;
  border-radius: 18px;
  overflow: hidden;
  cursor: pointer;
  background:
    radial-gradient(circle at top left, rgba(103, 194, 58, 0.12), transparent 36%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 249, 251, 0.98));
  border: 1px solid var(--collection-card-surface-color);
  border-left-width: 3px;
  border-left-style: solid;
  border-left-color: var(--collection-card-accent-color);
}

.collection-card.is-selected {
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.22);
  border-color: rgba(103, 194, 58, 0.26);
  border-left-color: var(--el-color-primary);
}

.collection-card.is-archived {
  --collection-card-accent-color: #6d747e;
  --collection-card-surface-color: rgba(95, 103, 114, 0.12);
  background:
    radial-gradient(circle at top left, rgba(95, 103, 114, 0.16), transparent 38%),
    linear-gradient(180deg, rgba(245, 247, 250, 0.98), rgba(237, 240, 244, 0.98));
  border-color: var(--collection-card-surface-color);
  border-left-width: 3px;
  border-left-color: var(--collection-card-accent-color);
}

.collection-card.is-archived.is-selected {
  border-left-color: var(--el-color-primary);
}

.collection-card:hover {
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
}

.collection-card.is-multi-select {
  cursor: pointer;
}

:deep(.collection-card .el-card__body) {
  padding: 18px;
}

.select-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  z-index: 2;
}

.select-indicator.is-selected {
  background: var(--el-color-primary);
  color: #fff;
}

.collection-card-layout {
  display: block;
}

.collection-card-main {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.collection-title-block {
  min-width: 0;
}

.collection-title {
  font-size: 17px;
  font-weight: 700;
  line-height: 1.45;
  color: var(--el-text-color-primary);
  word-break: break-word;
  padding-right: 32px;
}

.collection-card.is-archived .collection-title {
  color: var(--el-text-color-regular);
}

.collection-preview {
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-regular);
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: pre-wrap;
  word-break: break-word;
}

.collection-card.is-archived .collection-preview {
  color: var(--el-text-color-secondary);
}

.collection-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-size: 12px;
}

.collection-meta-content {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.collection-meta-group {
  min-width: 0;
  display: flex;
  flex: 0 0 auto;
}

.collection-meta-group--secondary {
  flex: 1;
  min-width: 0;
}

.collection-meta-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.collection-meta-divider {
  display: inline-flex;
  align-items: center;
  color: var(--el-text-color-placeholder);
  line-height: 1;
  align-self: center;
  transform: translateY(-1px);
}

.collection-meta-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.collection-card-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.action-button {
  min-width: 72px;
  margin: 0;
}

.collection-load-trigger {
  width: 100%;
  height: 1px;
}

.collection-list-status {
  padding: 16px 0 4px;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.collection-list-status--end {
  color: var(--el-text-color-placeholder);
}

.muted-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.dialog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.asset-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.existing-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.existing-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.existing-tag:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.required-mark {
  color: var(--el-color-danger);
  margin-left: 2px;
}

.required-hint {
  margin-top: -6px;
  margin-bottom: 18px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-color-danger);
}

.asset-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.asset-folder-summary {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.asset-folder-summary__path {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
  text-align: left;
  color: var(--el-text-color-primary);
  font-size: 13px;
  line-height: 1.6;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.asset-folder-summary__path:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-fill-color-light);
}

.asset-empty {
  width: 100%;
  padding: 16px;
  border: 1px dashed var(--el-border-color);
  border-radius: 10px;
  color: var(--el-text-color-secondary);
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.asset-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
}

.asset-info {
  min-width: 0;
}

.asset-name {
  color: var(--el-color-primary);
  text-decoration: none;
}

.asset-meta {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.asset-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.hidden-upload {
  display: none;
}

.dialog-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.delete-confirm-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.delete-confirm-checkbox {
  margin-top: 16px;
  padding-left: 52px;
}

.delete-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.status-filter-popover) {
  padding: 8px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid var(--el-border-color-lighter) !important;
}

:global(html.dark) :deep(.status-filter-popover) {
  background-color: var(--el-bg-color) !important;
  border-color: var(--el-border-color) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

:global(html.dark) .status-filter-item:hover {
  background-color: var(--bg-hover);
}

:global(html.dark) .status-filter-item.is-selected {
  background-color: rgba(103, 194, 58, 0.15);
}

:global(html.dark) .status-filter-text {
  color: var(--text-primary);
}

:global(.dark) .page-container .page-title,
:global(.dark) .page-container .page-title span,
:global(.dark) .page-container .page-title .el-icon {
  color: #fff !important;
}

:global(.dark) .page-container .collection-card {
  background:
    radial-gradient(circle at top left, rgba(103, 194, 58, 0.16), transparent 38%),
    linear-gradient(180deg, rgba(34, 39, 46, 0.98), rgba(24, 28, 34, 0.98));
  border-color: rgba(255, 255, 255, 0.06);
  border-left-color: var(--collection-card-accent-color) !important;
}

:global(.dark) .page-container .collection-card.is-archived {
  background:
    radial-gradient(circle at top left, rgba(160, 162, 167, 0.16), transparent 38%),
    linear-gradient(180deg, rgba(48, 52, 59, 0.98), rgba(38, 42, 48, 0.98));
  border-color: rgba(255, 255, 255, 0.08);
  border-left-color: #5f6772 !important;
}

:global(.dark) .page-container .collection-title,
:global(.dark) .page-container .collection-card.is-archived .collection-title {
  color: #fff !important;
}

:global(.dark) .page-container .collection-card.is-selected {
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.32);
  border-left-color: var(--el-color-primary);
}

:global(.dark) .page-container .multi-select-toolbar {
  background: rgba(24, 24, 28, 0.92);
  border-color: rgb(var(--el-color-primary-rgb) / 0.32);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
}

@media (--mobile-viewport) {
  .page-container {
    padding: 16px 16px 136px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .status-bar {
    align-items: stretch;
  }

  .dialog-grid {
    grid-template-columns: 1fr;
  }

  .todo-search-input {
    width: 100%;
    max-width: none;
  }

  .multi-select-toolbar {
    width: calc(100vw - 24px);
    bottom: calc(12px + var(--app-safe-area-bottom));
    flex-direction: column;
    align-items: stretch;
  }

  .multi-select-toolbar__actions {
    width: 100%;
  }

  .collection-meta-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .collection-meta-content {
    flex-wrap: wrap;
  }

  .collection-meta-divider {
    display: none;
  }

  .collection-card-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .action-button {
    min-width: 0;
    flex: 1 1 calc(33.333% - 6px);
  }

  .asset-item {
    flex-direction: column;
    align-items: stretch;
  }

  .asset-actions {
    justify-content: flex-start;
  }

  .dialog-footer-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .asset-folder-summary,
  .asset-folder-summary__path {
    width: 100%;
  }
}
</style>

