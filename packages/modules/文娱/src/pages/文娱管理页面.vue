<script setup lang="ts">
import { Delete, Edit, Link, Plus, Search, Star, Upload } from '@element-plus/icons-vue'
import { 获取API错误消息 } from '@personal-system/api'
import { PageSectionShell, TagInlineInput } from '@personal-system/ui'
import {
  ElAutocomplete,
  ElButton,
  ElCard,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElPopconfirm,
  ElRate,
  ElSelect,
  ElSpace,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTooltip,
} from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  从外部URL导入封面,
  从外部导入文娱,
  创建文娱,
  删除文娱,
  搜索外部文娱,
  上传文娱封面,
  更新文娱,
  获取文娱个人标签统计,
  获取文娱列表,
  获取文娱创作者建议,
  获取文娱子分类统计,
  获取文娱标签统计,
} from '../api'
import { 获取文娱状态标签, 获取文娱状态选项 } from '../display'
import { 获取评分展示 } from '../rating'
import type {
  ExternalMediaCandidate,
  MediaCreatorSuggestion,
  MediaListQuery,
  MediaPayload,
  MediaRecord,
  MediaStatus,
  MediaType,
} from '../types'

interface MediaFormState {
  title: string
  original_title: string
  media_type: MediaType
  status: MediaStatus
  rating: number | null
  creator: string
  genres_text: string
  tags_text: string
  personal_tags_text: string
  summary: string
  description: string
  cover_file_name: string
  external_cover_url: string
  external_cover_provider: string
  external_cover_id: string
  is_visible: boolean
}

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const keyword = ref('')
const records = ref<MediaRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const selectedGenre = ref('')
const selectedTag = ref('')
const selectedPersonalTag = ref('')
const selectedType = ref<MediaType | ''>('')
const selectedStatus = ref<MediaStatus | ''>('')
const allAvailableGenres = ref<string[]>([])
const filterAvailableGenres = ref<string[]>([])
const formAvailableGenres = ref<string[]>([])
const allAvailableTags = ref<string[]>([])
const filterAvailableTags = ref<string[]>([])
const formAvailableTags = ref<string[]>([])
const allAvailablePersonalTags = ref<string[]>([])
const filterAvailablePersonalTags = ref<string[]>([])
const formAvailablePersonalTags = ref<string[]>([])
const coverSearchKeyword = ref('')
const coverSearchLoading = ref(false)
const coverSearchResults = ref<ExternalMediaCandidate[]>([])
const localCoverInputRef = ref<HTMLInputElement | null>(null)
const localCoverFile = ref<File | null>(null)
const localCoverPreviewUrl = ref('')
const currentId = ref('')
const currentCoverFileName = ref('')
const currentCoverPreviewUrl = ref('')
const currentExternalCoverUrl = ref('')
const currentExternalCoverProvider = ref('')
const currentExternalCoverId = ref('')
const creatorSuggestionLoading = ref(false)
const creatorSuggestions = ref<MediaCreatorSuggestion[]>([])
let creatorSuggestionRequestId = 0
const route = useRoute()
const router = useRouter()

const 主分类选项: Array<{ label: string, value: MediaType }> = [
  { label: '游戏', value: 'game' },
  { label: '小说', value: 'novel' },
  { label: '书籍', value: 'book' },
  { label: '动画', value: 'anime' },
  { label: '漫画', value: 'comic' },
  { label: '电影', value: 'movie' },
  { label: '剧集', value: 'tv' },
  { label: '音乐', value: 'music' },
  { label: '其他', value: 'other' },
]

const 状态选项 = computed(() => 获取文娱状态选项(selectedType.value))
const 表单状态选项 = computed(() => 获取文娱状态选项(form.value.media_type))
const 评分列宽度 = 180

function 创建空表单(): MediaFormState {
  return {
    title: '',
    original_title: '',
    media_type: 'anime',
    status: 'done',
    rating: null,
    creator: '',
    genres_text: '',
    tags_text: '',
    personal_tags_text: '',
    summary: '',
    description: '',
    cover_file_name: '',
    external_cover_url: '',
    external_cover_provider: '',
    external_cover_id: '',
    is_visible: true,
  }
}

const form = ref<MediaFormState>(创建空表单())
const 表单评分星数 = computed({
  get() {
    if (form.value.rating == null || form.value.rating <= 3) {
      return 0
    }
    return 获取评分展示(form.value.rating).starValue
  },
  set(value: number) {
    const 标准化星数 = Math.max(0, Math.min(6, Math.round(value * 2) / 2))
    form.value.rating = 标准化星数 <= 0 ? null : Math.round(标准化星数 * 2 + 3)
  },
})

const 对话框标题 = computed(() => dialogMode.value === 'create' ? '新增文娱条目' : '编辑文娱条目')
const 可选子分类建议 = computed(() => 获取可用建议项(form.value.genres_text, formAvailableGenres.value))
const 可选标签建议 = computed(() => 获取可用建议项(form.value.tags_text, formAvailableTags.value))
const 可选个人标签建议 = computed(() => 获取可用建议项(form.value.personal_tags_text, formAvailablePersonalTags.value))
const 不属于当前主分类的子分类 = computed(() => 获取跨分类提示项(
  form.value.genres_text,
  allAvailableGenres.value,
  formAvailableGenres.value,
))
const 不属于当前主分类的标签 = computed(() => 获取跨分类提示项(
  form.value.tags_text,
  allAvailableTags.value,
  formAvailableTags.value,
))
const 不属于当前主分类的个人标签 = computed(() => 获取跨分类提示项(
  form.value.personal_tags_text,
  allAvailablePersonalTags.value,
  formAvailablePersonalTags.value,
))
const 当前封面预览地址 = computed(
  () => localCoverPreviewUrl.value || form.value.external_cover_url || currentCoverPreviewUrl.value,
)
const 当前封面显示文本 = computed(
  () => localCoverFile.value?.name
    || form.value.cover_file_name
    || form.value.external_cover_url
    || (currentCoverPreviewUrl.value ? '已保存封面' : ''),
)
const 当前是否存在待上传封面 = computed(() => {
  if (localCoverFile.value) {
    return true
  }
  if (!form.value.external_cover_url) {
    return false
  }
  if (dialogMode.value === 'create' || !currentId.value) {
    return true
  }
  return form.value.external_cover_url !== currentExternalCoverUrl.value
    || form.value.external_cover_provider !== currentExternalCoverProvider.value
    || form.value.external_cover_id !== currentExternalCoverId.value
})

function 解析标签文本(text: string): string[] {
  return text
    .replaceAll('，', ',')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function 获取可用建议项(currentText: string, existingItems: string[]): string[] {
  const currentItems = new Set(解析标签文本(currentText))
  return existingItems.filter(item => !currentItems.has(item))
}

function 获取跨分类提示项(currentText: string, allItems: string[], scopedItems: string[]): string[] {
  const allItemSet = new Set(allItems)
  const scopedItemSet = new Set(scopedItems)
  return 解析标签文本(currentText).filter(item => allItemSet.has(item) && !scopedItemSet.has(item))
}

function 追加建议项(currentText: string, item: string): string {
  const items = 解析标签文本(currentText)
  if (!items.includes(item)) {
    items.push(item)
  }
  return items.join(', ')
}

function 构建请求体(): MediaPayload {
  return {
    title: form.value.title.trim(),
    original_title: form.value.original_title.trim() || null,
    media_type: form.value.media_type,
    status: form.value.status,
    rating: form.value.rating,
    creator: form.value.creator.trim() || null,
    genres: 解析标签文本(form.value.genres_text),
    tags: 解析标签文本(form.value.tags_text),
    personal_tags: 解析标签文本(form.value.personal_tags_text),
    summary: form.value.summary.trim() || null,
    description: form.value.description.trim() || null,
    is_visible: form.value.is_visible,
  }
}

function 释放本地封面预览() {
  if (!localCoverPreviewUrl.value) {
    return
  }
  URL.revokeObjectURL(localCoverPreviewUrl.value)
  localCoverPreviewUrl.value = ''
}

function 清理本地封面选择() {
  释放本地封面预览()
  localCoverFile.value = null
  if (localCoverInputRef.value) {
    localCoverInputRef.value.value = ''
  }
}

function 恢复当前封面信息() {
  form.value.cover_file_name = currentCoverFileName.value
  form.value.external_cover_url = currentExternalCoverUrl.value
  form.value.external_cover_provider = currentExternalCoverProvider.value
  form.value.external_cover_id = currentExternalCoverId.value
}

function 重置表单() {
  清理本地封面选择()
  form.value = 创建空表单()
  currentId.value = ''
  currentCoverFileName.value = ''
  currentCoverPreviewUrl.value = ''
  currentExternalCoverUrl.value = ''
  currentExternalCoverProvider.value = ''
  currentExternalCoverId.value = ''
  coverSearchKeyword.value = ''
  coverSearchResults.value = []
}

function 获取评分摘要(rating: number) {
  return 获取评分展示(rating).label
}

function 获取评分星数(rating: number) {
  return 获取评分展示(rating).starValue
}

function 获取表单评分说明() {
  if (form.value.rating == null) {
    return '未评分'
  }
  return 获取评分展示(form.value.rating).label
}

function 选择表单评分(rating: number | null) {
  form.value.rating = rating
}

function 获取标签溢出提示(items: string[]): string {
  return items.join('、')
}

function 从记录填充表单(record: MediaRecord) {
  const 已有封面名称 = record.primary_cover_asset?.original_name ?? record.primary_cover_asset?.external_url ?? ''
  const 已有外部封面地址 = record.primary_cover_asset?.external_url ?? ''
  form.value = {
    title: record.title,
    original_title: record.original_title ?? '',
    media_type: record.media_type,
    status: record.status,
    rating: record.rating,
    creator: record.creator ?? '',
    genres_text: record.genres.join(', '),
    tags_text: record.tags.join(', '),
    personal_tags_text: (record.personal_tags || []).join(', '),
    summary: record.summary ?? '',
    description: record.description ?? '',
    cover_file_name: 已有封面名称,
    external_cover_url: 已有外部封面地址,
    external_cover_provider: record.primary_cover_asset?.source_provider ?? '',
    external_cover_id: record.primary_cover_asset?.source_asset_id ?? '',
    is_visible: record.is_visible,
  }
  清理本地封面选择()
  currentId.value = record.id
  currentCoverFileName.value = 已有封面名称
  currentCoverPreviewUrl.value = record.primary_cover_asset?.thumbnail_url ?? record.primary_cover_asset?.url ?? ''
  currentExternalCoverUrl.value = 已有外部封面地址
  currentExternalCoverProvider.value = record.primary_cover_asset?.source_provider ?? ''
  currentExternalCoverId.value = record.primary_cover_asset?.source_asset_id ?? ''
}

async function 加载筛选项() {
  const [genres, tags, personalTags] = await Promise.all([
    获取文娱子分类统计(),
    获取文娱标签统计(),
    获取文娱个人标签统计(),
  ])
  allAvailableGenres.value = genres.map((item) => item.name)
  allAvailableTags.value = tags.map((item) => item.name)
  allAvailablePersonalTags.value = personalTags.map((item) => item.name)
  if (selectedType.value) {
    await Promise.all([
      加载筛选子分类选项(selectedType.value),
      加载筛选标签选项(selectedType.value),
      加载筛选个人标签选项(selectedType.value),
    ])
    return
  }
  filterAvailableGenres.value = [...allAvailableGenres.value]
  filterAvailableTags.value = [...allAvailableTags.value]
  filterAvailablePersonalTags.value = [...allAvailablePersonalTags.value]
}

async function 加载筛选子分类选项(mediaType?: MediaType | '') {
  try {
    const genres = await 获取文娱子分类统计(mediaType || undefined)
    filterAvailableGenres.value = genres.map(item => item.name)
    if (selectedGenre.value && !filterAvailableGenres.value.includes(selectedGenre.value)) {
      selectedGenre.value = ''
    }
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载筛选子分类失败'))
    filterAvailableGenres.value = []
  }
}

async function 加载筛选标签选项(mediaType?: MediaType | '') {
  try {
    const tags = await 获取文娱标签统计(mediaType || undefined)
    filterAvailableTags.value = tags.map(item => item.name)
    if (selectedTag.value && !filterAvailableTags.value.includes(selectedTag.value)) {
      selectedTag.value = ''
    }
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载筛选标签失败'))
    filterAvailableTags.value = []
  }
}

async function 加载筛选个人标签选项(mediaType?: MediaType | '') {
  try {
    const tags = await 获取文娱个人标签统计(mediaType || undefined)
    filterAvailablePersonalTags.value = tags.map(item => item.name)
    if (selectedPersonalTag.value && !filterAvailablePersonalTags.value.includes(selectedPersonalTag.value)) {
      selectedPersonalTag.value = ''
    }
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载个人标签失败'))
    filterAvailablePersonalTags.value = []
  }
}

async function 加载表单子分类建议(mediaType: MediaType) {
  try {
    const genres = await 获取文娱子分类统计(mediaType)
    formAvailableGenres.value = genres.map(item => item.name)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载子分类建议失败'))
    formAvailableGenres.value = []
  }
}

async function 加载表单标签建议(mediaType: MediaType) {
  try {
    const tags = await 获取文娱标签统计(mediaType)
    formAvailableTags.value = tags.map(item => item.name)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载标签建议失败'))
    formAvailableTags.value = []
  }
}

async function 加载表单个人标签建议(mediaType: MediaType) {
  try {
    const tags = await 获取文娱个人标签统计(mediaType)
    formAvailablePersonalTags.value = tags.map(item => item.name)
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载个人标签建议失败'))
    formAvailablePersonalTags.value = []
  }
}

async function 加载列表() {
  loading.value = true
  try {
    const query: MediaListQuery = {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim(),
      media_type: selectedType.value,
      status: selectedStatus.value,
      genre: selectedGenre.value || undefined,
      tag: selectedTag.value || undefined,
      personal_tag: selectedPersonalTag.value || undefined,
    }
    const response = await 获取文娱列表(query)
    records.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载文娱列表失败'))
  } finally {
    loading.value = false
  }
}

async function 搜索外部作品() {
  const search = coverSearchKeyword.value.trim()
  if (!search) {
    coverSearchResults.value = []
    return
  }
  coverSearchLoading.value = true
  try {
    const data = await 搜索外部文娱(search, form.value.media_type)
    coverSearchResults.value = data.items
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '搜索外部作品失败'))
  } finally {
    coverSearchLoading.value = false
  }
}

async function 尝试打开路由指定条目() {
  const mediaId = typeof route.query.media_id === 'string' ? route.query.media_id : ''
  if (!mediaId) {
    return
  }
  const target = records.value.find((record) => record.id === mediaId)
  if (target) {
    打开编辑(target)
    await router.replace({ query: { ...route.query, media_id: undefined } })
    return
  }
  ElMessage.warning('没有在当前列表中找到指定文娱条目')
}

function 填充外部候选(candidate: ExternalMediaCandidate) {
  清理本地封面选择()
  form.value.title = candidate.title
  form.value.original_title = candidate.original_title ?? ''
  form.value.media_type = candidate.media_type
  form.value.creator = candidate.creators.join('、')
  form.value.genres_text = candidate.genres.join(', ')
  form.value.tags_text = candidate.tags.join(', ')
  form.value.summary = candidate.summary ?? ''
  form.value.description = candidate.description ?? ''
  form.value.external_cover_url = candidate.cover_url ?? candidate.thumbnail_url ?? ''
  form.value.external_cover_provider = candidate.provider
  form.value.external_cover_id = candidate.external_id
  form.value.cover_file_name = candidate.cover_url ? `${candidate.provider}:${candidate.external_id}` : ''
}

function 仅更新外部候选封面(candidate: ExternalMediaCandidate) {
  清理本地封面选择()
  form.value.external_cover_url = candidate.cover_url ?? candidate.thumbnail_url ?? ''
  form.value.external_cover_provider = candidate.provider
  form.value.external_cover_id = candidate.external_id
  form.value.cover_file_name = form.value.external_cover_url
    ? `${candidate.provider}:${candidate.external_id}`
    : ''
  console.info('[MediaManage] 已从搜索结果选择待上传封面', {
    provider: candidate.provider,
    externalId: candidate.external_id,
    title: candidate.title,
    coverUrl: form.value.external_cover_url || null,
  })
}

function 打开本地封面选择() {
  localCoverInputRef.value?.click()
}

function 处理本地封面变更(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }
  const isImage = file.type.startsWith('image/') || /\.(avif|bmp|gif|heic|heif|ico|jpe?g|png|svg|tiff?|webp)$/i.test(file.name)
  if (!isImage) {
    ElMessage.warning('封面只允许上传图片文件')
    input.value = ''
    return
  }
  清理本地封面选择()
  localCoverFile.value = file
  localCoverPreviewUrl.value = URL.createObjectURL(file)
  form.value.cover_file_name = file.name
  form.value.external_cover_url = ''
  form.value.external_cover_provider = ''
  form.value.external_cover_id = ''
  console.info('[MediaManage] 已选择本地封面', {
    name: file.name,
    size: file.size,
    type: file.type || 'unknown',
  })
}

function 清除封面文件() {
  清理本地封面选择()
  if (dialogMode.value === 'edit' && currentId.value) {
    恢复当前封面信息()
    return
  }
  form.value.cover_file_name = ''
  form.value.external_cover_url = ''
  form.value.external_cover_provider = ''
  form.value.external_cover_id = ''
}

async function 上传已选择本地封面(mediaId: string, file: File) {
  console.info('[MediaManage] 开始上传本地封面', {
    mediaId,
    name: file.name,
    size: file.size,
    type: file.type || 'unknown',
  })
  await 上传文娱封面(mediaId, file)
}

async function 加载创作者建议(keyword = '') {
  const requestId = ++creatorSuggestionRequestId
  creatorSuggestionLoading.value = true
  try {
    const suggestions = await 获取文娱创作者建议(keyword, 10)
    if (requestId !== creatorSuggestionRequestId) {
      return []
    }
    creatorSuggestions.value = suggestions
    return suggestions
  } catch (error) {
    if (requestId === creatorSuggestionRequestId) {
      ElMessage.error(获取API错误消息(error, '加载创作者建议失败'))
    }
    return []
  } finally {
    if (requestId === creatorSuggestionRequestId) {
      creatorSuggestionLoading.value = false
    }
  }
}

async function 查询创作者建议(
  queryString: string,
  callback: (items: Array<{ value: string, count: number }>) => void,
) {
  const suggestions = queryString.trim() || creatorSuggestions.value.length === 0
    ? await 加载创作者建议(queryString)
    : creatorSuggestions.value
  callback(
    suggestions.map((item) => ({
      value: item.name,
      count: item.count,
    })),
  )
}

function 选择创作者建议(item: Record<string, unknown>) {
  if (typeof item.value === 'string') {
    form.value.creator = item.value
  }
}

function 打开新增() {
  dialogMode.value = 'create'
  重置表单()
  dialogVisible.value = true
  void 加载创作者建议()
  void Promise.all([
    加载表单子分类建议(form.value.media_type),
    加载表单标签建议(form.value.media_type),
    加载表单个人标签建议(form.value.media_type),
  ])
}

function 打开编辑(record: MediaRecord) {
  dialogMode.value = 'edit'
  从记录填充表单(record)
  dialogVisible.value = true
  void 加载创作者建议(record.creator ?? '')
  void Promise.all([
    加载表单子分类建议(form.value.media_type),
    加载表单标签建议(form.value.media_type),
    加载表单个人标签建议(form.value.media_type),
  ])
}

async function 提交表单() {
  if (!form.value.title.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }
  saving.value = true
  try {
    const payload = 构建请求体()
    const selectedLocalCover = localCoverFile.value
    if (dialogMode.value === 'create') {
      if (form.value.external_cover_provider && form.value.external_cover_id) {
        const importedRecord = await 从外部导入文娱({
          provider: form.value.external_cover_provider,
          external_id: form.value.external_cover_id,
          status: form.value.status,
          rating: form.value.rating,
          is_visible: form.value.is_visible,
          localize_cover: Boolean(form.value.external_cover_url),
        })
        const personalTags = 解析标签文本(form.value.personal_tags_text)
        if (personalTags.length > 0) {
          await 更新文娱(importedRecord.id, { personal_tags: personalTags })
        }
      } else {
        const record = await 创建文娱(payload)
        if (selectedLocalCover) {
          await 上传已选择本地封面(record.id, selectedLocalCover)
        } else if (form.value.external_cover_url) {
          await 从外部URL导入封面(record.id, {
            external_url: form.value.external_cover_url,
            source_provider: form.value.external_cover_provider || null,
            source_asset_id: form.value.external_cover_id || null,
            original_name: `${form.value.title.trim() || 'cover'}.jpg`,
            set_primary: true,
          })
        }
      }
      ElMessage.success('文娱条目已创建')
    } else {
      await 更新文娱(currentId.value, payload)
      if (selectedLocalCover) {
        await 上传已选择本地封面(currentId.value, selectedLocalCover)
      } else if (form.value.external_cover_url && form.value.external_cover_url !== currentExternalCoverUrl.value) {
        await 从外部URL导入封面(currentId.value, {
          external_url: form.value.external_cover_url,
          source_provider: form.value.external_cover_provider || null,
          source_asset_id: form.value.external_cover_id || null,
          original_name: `${form.value.title.trim() || 'cover'}.jpg`,
          set_primary: true,
        })
      }
      ElMessage.success('文娱条目已更新')
    }
    dialogVisible.value = false
    await Promise.all([加载列表(), 加载筛选项()])
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '保存文娱条目失败'))
  } finally {
    saving.value = false
  }
}

async function 执行删除(id: string) {
  try {
    await 删除文娱(id)
    ElMessage.success('文娱条目已删除')
    await Promise.all([加载列表(), 加载筛选项()])
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '删除文娱条目失败'))
  }
}

watch([selectedType, selectedStatus, selectedGenre, selectedTag, selectedPersonalTag], () => {
  page.value = 1
  void 加载列表()
})

watch(
  selectedType,
  (mediaType) => {
    void Promise.all([
      加载筛选子分类选项(mediaType),
      加载筛选标签选项(mediaType),
      加载筛选个人标签选项(mediaType),
    ])
  },
)

watch(
  () => form.value.media_type,
  (mediaType) => {
    if (!dialogVisible.value) {
      return
    }
    void Promise.all([
      加载表单子分类建议(mediaType),
      加载表单标签建议(mediaType),
      加载表单个人标签建议(mediaType),
    ])
  },
)

onMounted(async () => {
  await Promise.all([加载列表(), 加载筛选项()])
  await 尝试打开路由指定条目()
})

onBeforeUnmount(() => {
  释放本地封面预览()
})
</script>

<template>
  <div class="media-page">
    <PageSectionShell title="作品推荐" :icon="Star" title-tag="h2">
      <template #header-extra>
        <ElSpace>
          <ElButton type="primary" :icon="Plus" @click="打开新增">新增条目</ElButton>
        </ElSpace>
      </template>

      <ElCard shadow="never" class="media-panel">
        <div class="media-toolbar">
          <ElInput v-model="keyword" placeholder="搜索名称、原名、作者或简介" clearable @keyup.enter="加载列表">
            <template #prefix>
              <Search />
            </template>
          </ElInput>
          <ElSelect v-model="selectedType" clearable placeholder="主分类">
            <ElOption v-for="item in 主分类选项" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
          <ElSelect v-model="selectedStatus" clearable placeholder="状态">
            <ElOption v-for="item in 状态选项" :key="item.value" :label="item.label" :value="item.value" />
          </ElSelect>
          <ElSelect v-model="selectedGenre" clearable filterable placeholder="外部分类">
            <ElOption v-for="item in filterAvailableGenres" :key="item" :label="item" :value="item" />
          </ElSelect>
          <ElSelect v-model="selectedTag" clearable filterable placeholder="外部标签">
            <ElOption v-for="item in filterAvailableTags" :key="item" :label="item" :value="item" />
          </ElSelect>
          <ElSelect v-model="selectedPersonalTag" clearable filterable placeholder="个人标签">
            <ElOption v-for="item in filterAvailablePersonalTags" :key="item" :label="item" :value="item" />
          </ElSelect>
          <ElButton type="primary" @click="加载列表">搜索</ElButton>
        </div>

        <ElTable v-loading="loading" :data="records" class="media-table" empty-text="暂无文娱条目">
          <ElTableColumn label="名称" min-width="280">
            <template #default="{ row }: { row: MediaRecord }">
              <div class="media-title-cell">
                <img v-if="row.primary_cover_asset?.thumbnail_url || row.primary_cover_asset?.url" :src="row.primary_cover_asset?.thumbnail_url || row.primary_cover_asset?.url || ''" :alt="row.title" class="media-cover" >
                <div class="media-title-meta">
                  <div class="media-title">{{ row.title }}</div>
                  <div v-if="row.original_title" class="media-original-title">{{ row.original_title }}</div>
                </div>
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn label="主分类" width="100">
            <template #default="{ row }: { row: MediaRecord }">
              <ElTag>{{ 主分类选项.find((item) => item.value === row.media_type)?.label || row.media_type }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="状态" width="140">
            <template #default="{ row }: { row: MediaRecord }">
              {{ 获取文娱状态标签(row.media_type, row.status) }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="评分" :width="评分列宽度">
            <template #default="{ row }: { row: MediaRecord }">
              <span v-if="row.rating" class="media-rating-cell">
                <ElRate
                  :model-value="获取评分星数(row.rating)"
                  disabled
                  allow-half
                  :max="6"
                  class="media-rating-cell__stars"
                />
                <span class="media-rating-cell__text">{{ 获取评分摘要(row.rating) }}</span>
              </span>
              <span v-else>-</span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="创作者" min-width="160" prop="creator" />
          <ElTableColumn label="外部分类" min-width="220">
            <template #default="{ row }: { row: MediaRecord }">
              <ElSpace wrap>
                <ElTag v-for="genre in row.genres.slice(0, 4)" :key="genre" size="small" effect="plain" type="primary">{{ genre }}</ElTag>
                <ElTooltip v-if="row.genres.length > 4" :content="获取标签溢出提示(row.genres)" placement="top">
                  <ElTag size="small" effect="plain" type="info">+{{ row.genres.length - 4 }}</ElTag>
                </ElTooltip>
              </ElSpace>
            </template>
          </ElTableColumn>
          <ElTableColumn label="外部标签" min-width="220">
            <template #default="{ row }: { row: MediaRecord }">
              <ElSpace wrap>
                <ElTag v-for="tag in row.tags.slice(0, 4)" :key="tag" size="small" type="warning" effect="plain">{{ tag }}</ElTag>
                <ElTooltip v-if="row.tags.length > 4" :content="获取标签溢出提示(row.tags)" placement="top">
                  <ElTag size="small" type="warning" effect="plain">+{{ row.tags.length - 4 }}</ElTag>
                </ElTooltip>
              </ElSpace>
            </template>
          </ElTableColumn>
          <ElTableColumn label="个人标签" min-width="220">
            <template #default="{ row }: { row: MediaRecord }">
              <ElSpace wrap>
                <ElTag v-for="tag in (row.personal_tags || []).slice(0, 4)" :key="tag" size="small" type="success">{{ tag }}</ElTag>
                <ElTooltip v-if="(row.personal_tags || []).length > 4" :content="获取标签溢出提示(row.personal_tags || [])" placement="top">
                  <ElTag size="small" type="success">+{{ (row.personal_tags || []).length - 4 }}</ElTag>
                </ElTooltip>
              </ElSpace>
            </template>
          </ElTableColumn>
          <ElTableColumn label="公开" width="90">
            <template #default="{ row }: { row: MediaRecord }">
              <ElTag :type="row.is_visible ? 'success' : 'info'">{{ row.is_visible ? '是' : '否' }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn label="操作" width="140" fixed="right">
            <template #default="{ row }: { row: MediaRecord }">
              <ElSpace>
                <ElButton link type="primary" :icon="Edit" @click="打开编辑(row)">编辑</ElButton>
                <ElPopconfirm title="确认删除这条文娱记录？" @confirm="执行删除(row.id)">
                  <template #reference>
                    <ElButton link type="danger" :icon="Delete">删除</ElButton>
                  </template>
                </ElPopconfirm>
              </ElSpace>
            </template>
          </ElTableColumn>
        </ElTable>

        <div v-if="!loading && records.length === 0" class="media-empty">
          <ElEmpty description="还没有文娱条目" />
        </div>

        <div class="media-pagination">
          <span>共 {{ total }} 条</span>
          <ElSpace>
            <ElButton :disabled="page <= 1" @click="page -= 1; 加载列表()">上一页</ElButton>
            <span>第 {{ page }} 页</span>
            <ElButton :disabled="records.length < pageSize" @click="page += 1; 加载列表()">下一页</ElButton>
          </ElSpace>
        </div>
      </ElCard>
    </PageSectionShell>

    <ElDialog v-model="dialogVisible" :title="对话框标题" width="900px" destroy-on-close @closed="重置表单">
      <ElForm label-width="96px" class="media-form">
        <div class="media-form__grid">
          <ElFormItem label="名称" required>
            <ElInput v-model="form.title" maxlength="300" />
          </ElFormItem>
          <ElFormItem label="原名">
            <ElInput v-model="form.original_title" maxlength="300" />
          </ElFormItem>
          <ElFormItem label="主分类">
            <ElSelect v-model="form.media_type">
              <ElOption v-for="item in 主分类选项" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="状态">
            <ElSelect v-model="form.status">
              <ElOption v-for="item in 表单状态选项" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="评分">
            <div class="media-rating-editor">
              <div class="media-rating-editor__row">
                <div class="media-rating-editor__actions">
                  <ElTooltip content="未评分" placement="top">
                    <ElButton
                      size="small"
                      :type="form.rating == null ? 'primary' : 'default'"
                      plain
                      class="media-rating-editor__icon-button"
                      @click="选择表单评分(null)"
                    >
                      ∅
                    </ElButton>
                  </ElTooltip>
                  <ElTooltip content="雷区" placement="top">
                    <ElButton
                      size="small"
                      :type="form.rating === 1 ? 'danger' : 'default'"
                      plain
                      class="media-rating-editor__icon-button"
                      @click="选择表单评分(1)"
                    >
                      💣
                    </ElButton>
                  </ElTooltip>
                  <ElTooltip content="粪作" placement="top">
                    <ElButton
                      size="small"
                      :type="form.rating === 2 ? 'warning' : 'default'"
                      plain
                      class="media-rating-editor__icon-button"
                      @click="选择表单评分(2)"
                    >
                      💩
                    </ElButton>
                  </ElTooltip>
                  <ElTooltip content="0 星" placement="top">
                    <ElButton
                      size="small"
                      :type="form.rating === 3 ? 'primary' : 'default'"
                      plain
                      class="media-rating-editor__icon-button"
                      @click="选择表单评分(3)"
                    >
                      <ElIcon><Star /></ElIcon>
                    </ElButton>
                  </ElTooltip>
                </div>
                <span class="media-rating-editor__divider" aria-hidden="true">|</span>
                <div class="media-rating-editor__stars">
                  <ElRate
                    v-model="表单评分星数"
                    allow-half
                    :max="6"
                  />
                  <span class="media-rating-editor__text">{{ 获取表单评分说明() }}</span>
                </div>
              </div>
            </div>
          </ElFormItem>
          <ElFormItem label="创作者">
            <ElAutocomplete
              v-model="form.creator"
              maxlength="200"
              placeholder="作者 / 导演 / 工作室 / 开发商"
              :fetch-suggestions="查询创作者建议"
              :trigger-on-focus="true"
              :debounce="200"
              :fit-input-width="true"
              @select="选择创作者建议"
            >
              <template #default="{ item }: { item: { value: string, count: number } }">
                <div class="creator-suggestion">
                  <span>{{ item.value }}</span>
                  <span class="creator-suggestion__count">已使用 {{ item.count }} 次</span>
                </div>
              </template>
            </ElAutocomplete>
          </ElFormItem>
          <ElFormItem label="外部分类" class="media-form__full">
            <TagInlineInput v-model="form.genres_text" :existing-tags="formAvailableGenres" placeholder="多个值用逗号分隔" />
            <div v-if="可选子分类建议.length > 0" class="existing-tags">
              <ElTag
                v-for="genre in 可选子分类建议"
                :key="genre"
                size="small"
                effect="plain"
                class="existing-tag"
                @click="form.genres_text = 追加建议项(form.genres_text, genre)"
              >
                {{ genre }}
              </ElTag>
            </div>
            <div v-if="不属于当前主分类的子分类.length > 0" class="field-hint field-hint--warning">
              当前主分类下未见这些已有外部分类：{{ 不属于当前主分类的子分类.join('、') }}
            </div>
          </ElFormItem>
          <ElFormItem label="外部标签" class="media-form__full">
            <TagInlineInput v-model="form.tags_text" :existing-tags="formAvailableTags" placeholder="多个值用逗号分隔" />
            <div v-if="可选标签建议.length > 0" class="existing-tags">
              <ElTag
                v-for="tag in 可选标签建议"
                :key="tag"
                size="small"
                effect="plain"
                class="existing-tag"
                @click="form.tags_text = 追加建议项(form.tags_text, tag)"
              >
                {{ tag }}
              </ElTag>
            </div>
            <div v-if="不属于当前主分类的标签.length > 0" class="field-hint field-hint--warning">
              当前主分类下未见这些已有外部标签：{{ 不属于当前主分类的标签.join('、') }}
            </div>
          </ElFormItem>
          <ElFormItem label="个人标签" class="media-form__full">
            <TagInlineInput v-model="form.personal_tags_text" :existing-tags="formAvailablePersonalTags" placeholder="多个值用逗号分隔" />
            <div v-if="可选个人标签建议.length > 0" class="existing-tags">
              <ElTag
                v-for="tag in 可选个人标签建议"
                :key="tag"
                size="small"
                type="success"
                class="existing-tag"
                @click="form.personal_tags_text = 追加建议项(form.personal_tags_text, tag)"
              >
                {{ tag }}
              </ElTag>
            </div>
            <div v-if="不属于当前主分类的个人标签.length > 0" class="field-hint field-hint--warning">
              当前主分类下未见这些已有个人标签：{{ 不属于当前主分类的个人标签.join('、') }}
            </div>
          </ElFormItem>
          <ElFormItem label="简介" class="media-form__full">
            <ElInput v-model="form.summary" type="textarea" :rows="3" />
          </ElFormItem>
          <ElFormItem label="描述" class="media-form__full">
            <ElInput v-model="form.description" type="textarea" :rows="5" />
          </ElFormItem>
          <ElFormItem label="公开展示">
            <ElSwitch v-model="form.is_visible" />
          </ElFormItem>
          <ElFormItem label="封面" class="media-form__full">
            <div class="cover-picker">
              <div class="cover-picker__toolbar">
                <ElInput
                  v-model="coverSearchKeyword"
                  class="cover-picker__search-input"
                  placeholder="搜索 Bangumi、Google Books、AniList 等外部作品"
                  clearable
                  @keyup.enter="搜索外部作品"
                />
                <ElButton :icon="Search" :loading="coverSearchLoading" @click="搜索外部作品">搜索</ElButton>
                <ElButton :icon="Upload" @click="打开本地封面选择">上传封面</ElButton>
                <ElButton v-if="localCoverFile || form.external_cover_url" @click="清除封面文件">清除封面</ElButton>
              </div>
              <input
                ref="localCoverInputRef"
                type="file"
                accept="image/*,.avif,.bmp,.gif,.heic,.heif,.ico,.jpeg,.jpg,.png,.svg,.tif,.tiff,.webp"
                class="cover-picker__input"
                @change="处理本地封面变更"
              >
              <div v-if="当前封面预览地址 || 当前封面显示文本" class="cover-picker__selected">
                <img
                  v-if="当前封面预览地址"
                  :src="当前封面预览地址"
                  :alt="form.title || '封面预览'"
                  class="cover-picker__selected-thumb"
                >
                <div class="cover-picker__selected-meta">
                  <span class="cover-picker__selected-label">{{ 当前是否存在待上传封面 ? '待上传封面' : '当前封面' }}</span>
                  <span class="cover-picker__selected-value">{{ 当前封面显示文本 }}</span>
                </div>
              </div>
              <div v-if="coverSearchResults.length > 0" class="cover-picker__results">
                <div
                  v-for="candidate in coverSearchResults"
                  :key="`${candidate.provider}:${candidate.external_id}`"
                  class="cover-picker__item"
                  role="button"
                  tabindex="0"
                  @click="填充外部候选(candidate)"
                  @keydown.enter="填充外部候选(candidate)"
                  @keydown.space.prevent="填充外部候选(candidate)"
                >
                  <ElButton
                    class="cover-picker__cover-only-button"
                    size="small"
                    type="primary"
                    plain
                    @click.stop="仅更新外部候选封面(candidate)"
                  >
                    只更新封面
                  </ElButton>
                  <img v-if="candidate.thumbnail_url || candidate.cover_url" :src="candidate.thumbnail_url || candidate.cover_url || ''" :alt="candidate.title" class="cover-picker__thumb" >
                  <span class="cover-picker__title">{{ candidate.title }}</span>
                  <span class="cover-picker__meta">
                    <ElIcon><Link /></ElIcon>
                    {{ candidate.provider }}
                  </span>
                </div>
              </div>
            </div>
          </ElFormItem>
        </div>
      </ElForm>
      <template #footer>
        <ElSpace>
          <ElButton @click="dialogVisible = false">取消</ElButton>
          <ElButton type="primary" :loading="saving" @click="提交表单">保存</ElButton>
        </ElSpace>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.media-page {
  padding: 20px;
}

.media-panel {
  border-radius: 20px;
}

.media-toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1.4fr) repeat(5, minmax(120px, 1fr)) auto;
  gap: 12px;
  margin-bottom: 20px;
}

.media-table {
  width: 100%;
}

.media-title-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.media-cover {
  width: 52px;
  height: 72px;
  border-radius: 10px;
  object-fit: cover;
  background: #f5f5f5;
}

.media-title {
  font-weight: 600;
}

.media-original-title {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.media-rating-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.media-rating-cell__stars {
  --el-rate-icon-size: 14px;
}

.media-rating-cell__text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.media-rating-editor {
  width: 100%;
}

.media-rating-editor__row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.media-rating-editor__actions {
  display: flex;
  gap: 0px;
}

.media-rating-editor__icon-button {
  width: 20px;
  min-width: 20px;
  height: 20px;
  padding: 0;
  font-size: 16px;
}

.media-rating-editor__icon-button :deep(.el-icon) {
  font-size: 15px;
}

.media-rating-editor__divider {
  color: var(--el-border-color-darker);
  font-size: 14px;
  line-height: 1;
}

.media-rating-editor__stars {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.media-rating-editor__stars :deep(.el-rate) {
  --el-rate-icon-size: 18px;
}

.media-rating-editor__text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.media-empty {
  padding: 24px 0;
}

.creator-suggestion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.creator-suggestion__count {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.media-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
}

.media-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.media-form__full {
  grid-column: 1 / -1;
}

.media-form__full :deep(.el-form-item__content) {
  width: 100%;
}

.cover-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.existing-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.existing-tag {
  cursor: pointer;
}

.existing-tag:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.field-hint {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.field-hint--warning {
  color: var(--el-color-warning);
}

.cover-picker__toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.cover-picker__search-input {
  min-width: 0;
  width: 100%;
}

.cover-picker__search-input :deep(.el-input__wrapper) {
  width: 100%;
}

.cover-picker__selected {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.cover-picker__selected-thumb {
  width: 54px;
  height: 72px;
  border-radius: 8px;
  object-fit: cover;
  background: #f5f5f5;
  flex: none;
}

.cover-picker__selected-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.cover-picker__selected-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.cover-picker__selected-value {
  color: var(--el-text-color-primary);
  line-height: 1.5;
  word-break: break-all;
}

.cover-picker__input {
  display: none;
}

.cover-picker__results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  max-height: 260px;
  overflow: auto;
}

.cover-picker__item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  padding: 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.cover-picker__item:hover,
.cover-picker__item:focus-visible {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 8px 20px rgb(0 0 0 / 8%);
  transform: translateY(-1px);
}

.cover-picker__item:focus-visible {
  outline: 2px solid var(--el-color-primary-light-5);
  outline-offset: 2px;
}

.cover-picker__cover-only-button {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  border-color: rgb(255 255 255 / 55%);
  background: rgb(255 255 255 / 68%);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgb(0 0 0 / 12%);
}

.cover-picker__cover-only-button:hover,
.cover-picker__cover-only-button:focus-visible {
  border-color: rgb(255 255 255 / 72%);
  background: rgb(255 255 255 / 82%);
}

.cover-picker__item:hover .cover-picker__cover-only-button,
.cover-picker__item:focus-visible .cover-picker__cover-only-button,
.cover-picker__cover-only-button:focus-visible {
  opacity: 1;
  pointer-events: auto;
}

.cover-picker__thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 8px;
  background: #f5f5f5;
}

@media (max-width: 960px) {
  .media-toolbar {
    grid-template-columns: 1fr 1fr;
  }

  .media-form__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .media-page {
    padding: 12px;
  }

  .media-pagination,
  .cover-picker__toolbar {
    grid-template-columns: 1fr;
  }

  .cover-picker__toolbar > * {
    width: 100%;
  }

  .media-toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
