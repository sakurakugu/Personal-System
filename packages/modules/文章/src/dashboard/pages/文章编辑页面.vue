<script setup lang="ts">
import { Connection, Document, DocumentAdd, EditPen, MagicStick, View } from '@element-plus/icons-vue'
import {
  ElButton,
  ElDrawer,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSpace,
  ElSelect,
  ElSkeleton,
  ElTag,
} from 'element-plus'
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { 获取API错误消息 } from '@personal-system/api'
import { PageSectionShell, SegmentedSwitch } from '@personal-system/ui'
import { 使用保存快捷键 } from '../../使用保存快捷键'
import { 使用视口 } from '../../使用视口'
import { 使用文章主题状态 } from '../../theme'
import { 解析管理文件URL地址 } from '../../managedFile'
import { 删除文件 as 删除管理文件 } from '../../files-api'
import {
  创建文章,
  创建文章草稿,
  创建分类,
  创建标签,
  AI润色文章正文,
  生成文章AI元信息建议,
  获取文章图片,
  根据ID获取我的文章,
  更新文章,
  上传文章图片,
} from '../../api'
import MarkdownRenderer from '../../components/Markdown渲染器.vue'
import MilkdownMarkdownEditor from '../../components/MilkdownMarkdown编辑器.vue'
import type {
  MilkdownMarkdownImagePayload,
  MilkdownMarkdown编辑器实例,
} from '../../components/MilkdownMarkdown编辑器.vue'
import { renderArticleMarkdown } from '../../markdown'
import { 使用文章分类存储 } from '../../taxonomy'
import { 从Markdown首行提取文章标题 } from '../../title'
import type {
  ArticleDraftPayload,
  ArticleAIContentPolishResult,
  ArticleAIMetadataSuggestion,
  ArticleAIRequestPayload,
  ArticleEditorPayload,
  ArticleImageRecord,
  ArticleRecord,
  ArticleUpdatePayload,
} from '../../types'
import ArticleImagePanel from '../components/文章图片面板.vue'
import { 使用编辑器快捷键 } from '../composables/使用编辑器快捷键'

const props = withDefaults(defineProps<{
  showBack?: boolean
  backTo?: string
}>(), {
  showBack: false,
  backTo: '/articles',
})

const route = useRoute()
const router = useRouter()
const themeStore = 使用文章主题状态()
const articleTaxonomyStore = 使用文章分类存储()
const 路由前缀 = computed(() => route.path.startsWith('/dashboard') ? '/dashboard' : '')

const MarkdownMindmap = defineAsyncComponent(() => import('../../components/Markdown思维导图.vue'))

const currentArticleId = ref('')
const isEdit = computed(() => currentArticleId.value.length > 0)
const loading = ref(false)
const saving = ref(false)
const formatting = ref(false)
const uploadingImageCount = ref(0)
const editorId = 'article-editor'
const editorRef = ref<MilkdownMarkdown编辑器实例>()
const editorWrapperRef = ref<globalThis.HTMLDivElement | null>(null)
const markdownOverlayRef = ref<globalThis.HTMLDivElement | null>(null)
const htmlOverlayRef = ref<globalThis.HTMLDivElement | null>(null)
const editorTheme = computed(() => (themeStore.isDark.value ? 'dark' : 'light'))
const isUploadingImages = computed(() => uploadingImageCount.value > 0)
const { isMobileViewport } = 使用视口()
type 预览类型 = 'preview' | 'html' | 'mindmap'
type 预览布局模式 = 'hidden' | 'split' | 'full'

const previewType = ref<预览类型>('preview')
const previewLayoutMode = ref<预览布局模式>('hidden')
const scrollSyncEnabled = ref(true)
const isMarkdownPreviewVisible = computed(() => previewType.value === 'preview' && previewLayoutMode.value !== 'hidden')
const isMarkdownSplitVisible = computed(() => previewType.value === 'preview' && previewLayoutMode.value === 'split')
const isMarkdownFullVisible = computed(() => previewType.value === 'preview' && previewLayoutMode.value === 'full')
const isHtmlPreviewVisible = computed(() => previewType.value === 'html' && previewLayoutMode.value !== 'hidden')
const isHtmlSplitVisible = computed(() => previewType.value === 'html' && previewLayoutMode.value === 'split')
const isHtmlFullVisible = computed(() => previewType.value === 'html' && previewLayoutMode.value === 'full')
const isMindmapPreviewVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value !== 'hidden')
const isMindmapSplitVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value === 'split')
const isMindmapFullVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value === 'full')
const 编辑器内容区顶部偏移 = ref(0)
const 编辑器内容区底部偏移 = ref(0)
const 编辑器内容区覆盖样式 = computed(() => ({
  '--editor-content-top-offset': `${编辑器内容区顶部偏移.value}px`,
  '--editor-content-bottom-offset': `${编辑器内容区底部偏移.value}px`,
}))
const previewTypeOptions = [
  { label: '预览', value: 'preview', icon: View },
  { label: 'HTML', value: 'html', title: 'HTML 源码预览', icon: Document },
  { label: '脑图', value: 'mindmap', icon: Connection },
] as const
const previewLayoutModeOptions = [
  { label: '关闭', value: 'hidden' },
  { label: '半边', value: 'split' },
  { label: '全部', value: 'full' },
] as const

let 编辑器尺寸观察器: globalThis.ResizeObserver | null = null
let 滚动同步清理列表: Array<() => void> = []
let 滚动同步帧 = 0
let 滚动同步初始化帧 = 0
let 当前滚动同步来源: 'editor' | 'preview' | null = null
let 文章加载序号 = 0
let 文章图片加载序号 = 0
const 站内文件链接正则 = /(https?:\/\/[^\s"'<>)]*\/files\/[^\s"'<>)]*|\/files\/[^\s"'<>)]*)/g

interface SelectOption {
  label: string
  value: string
}

const form = ref<ArticleEditorPayload>(buildEmptyForm())
const savedForm = ref<ArticleEditorPayload>(cloneFormPayload(form.value))
const articleImages = ref<ArticleImageRecord[]>([])
const articleImagesLoading = ref(false)
const deletingArticleImages = ref(false)
const selectedUnusedArticleImageIds = ref<string[]>([])
const articleImagePanelExpanded = ref(false)
const aiDrawerVisible = ref(false)
const aiLoading = ref(false)
const aiMetadataSuggestion = ref<ArticleAIMetadataSuggestion | null>(null)
const aiPolishResult = ref<ArticleAIContentPolishResult | null>(null)
const aiStatusMessage = ref('')

const articleStatusOptions = [
  { label: '私有', value: 'private' },
  { label: '登录可见', value: 'login_required' },
  { label: '公开', value: 'public' },
] as const

const categories = ref<SelectOption[]>([])
const tags = ref<SelectOption[]>([])
const isDirty = computed(() => buildFormSnapshot(form.value) !== buildFormSnapshot(savedForm.value))
const 已使用文章图片路径集合 = computed(() => 收集已使用文章图片路径(form.value.content, form.value.cover_url))
const 文章图片列表项 = computed(() => articleImages.value.map((image) => {
  const 图片路径 = 规范化站内文件路径(image.url)
  return {
    ...image,
    isUsed: 图片路径 !== null && 已使用文章图片路径集合.value.has(图片路径),
  }
}))
const 未使用文章图片列表 = computed(() => 文章图片列表项.value.filter((image) => !image.isUsed))
const 已使用文章图片数量 = computed(() => 文章图片列表项.value.length - 未使用文章图片列表.value.length)
const htmlPreviewContent = computed(() => renderArticleMarkdown(form.value.content).html)
const 文章图片桌面摘要 = computed(() => (
  `共 ${文章图片列表项.value.length} 张，已使用 ${已使用文章图片数量.value} 张，未使用 ${未使用文章图片列表.value.length} 张`
))
const 文章图片移动端摘要 = computed(() => (
  未使用文章图片列表.value.length > 0
    ? `共 ${文章图片列表项.value.length} 张，未使用 ${未使用文章图片列表.value.length} 张`
    : `共 ${文章图片列表项.value.length} 张`
))
const 已有分类名称列表 = computed(() => categories.value.map((item) => item.label))
const 已有标签名称列表 = computed(() => tags.value.map((item) => item.label))
const AI建议分类已存在 = computed(() => {
  const categoryName = aiMetadataSuggestion.value?.category_name?.trim()
  return Boolean(categoryName && categories.value.some((item) => item.label === categoryName))
})
const AI建议新标签列表 = computed(() => {
  const suggestion = aiMetadataSuggestion.value
  if (!suggestion) {
    return []
  }
  const existingNames = new Set(tags.value.map((item) => item.label))
  return suggestion.tag_names.filter((name) => !existingNames.has(name))
})

type MarkdownPrettier = {
  format: (
    source: string,
    options: {
      parser: 'markdown'
      plugins: unknown[]
    },
  ) => string | Promise<string>
}

type MarkdownPrettierContext = {
  prettier: MarkdownPrettier
  markdownPlugin: unknown
}

type MarkdownPrettierWindow = typeof window & {
  prettier?: MarkdownPrettier
  prettierPlugins?: {
    markdown?: unknown
  }
}

interface SaveArticleOptions {
  redirectAfterSave: boolean
  syncRouteAfterSave?: boolean
}

使用保存快捷键({
  enabled: () => !loading.value && !saving.value && !formatting.value && !isUploadingImages.value,
  onSave: () => {
    if (!isDirty.value) {
      ElMessage.info('没有可保存的更改')
      return
    }

    return saveArticle({ redirectAfterSave: false, syncRouteAfterSave: true })
  },
})

使用编辑器快捷键({
  editorRoot: editorWrapperRef,
  editorId,
  enabled: () => !loading.value && !saving.value && !formatting.value && !isUploadingImages.value,
  onFormatAndSave: formatAndSaveArticle,
  onRedo: () => editorRef.value?.redo(),
})

function getRouteArticleId(): string {
  const routeArticleId = route.params.id

  if (typeof routeArticleId === 'string') {
    return routeArticleId
  }

  if (Array.isArray(routeArticleId)) {
    return routeArticleId[0] ?? ''
  }

  return ''
}

async function loadEditorOptions() {
  await articleTaxonomyStore.ensureLoaded()
  const categoryRecords = articleTaxonomyStore.categories
  const tagRecords = articleTaxonomyStore.tags
  categories.value = categoryRecords.map((category) => ({ label: category.name, value: category.id }))
  tags.value = tagRecords.map((tag) => ({ label: tag.name, value: tag.id }))
}

async function handleCreateCategory() {
  try {
    const { value } = await ElMessageBox.prompt('请输入新分类名称', '新增分类', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPattern: /^\S.{0,98}$/,
      inputErrorMessage: '分类名称不能为空且最多 100 个字符',
    })
    const category = await 创建分类(value.trim())
    articleTaxonomyStore.upsertCategory(category)
    categories.value.push({ label: category.name, value: category.id })
    form.value.category_id = category.id
    ElMessage.success('分类创建成功')
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(获取API错误消息(error, '创建分类失败'))
  }
}

async function handleCreateTag() {
  try {
    const { value } = await ElMessageBox.prompt('请输入新标签名称', '新增标签', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPattern: /^\S.{0,58}$/,
      inputErrorMessage: '标签名称不能为空且最多 60 个字符',
    })
    const tag = await 创建标签(value.trim())
    articleTaxonomyStore.upsertTag(tag)
    tags.value.push({ label: tag.name, value: tag.id })
    if (!form.value.tag_ids.includes(tag.id)) {
      form.value.tag_ids.push(tag.id)
    }
    ElMessage.success('标签创建成功')
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(获取API错误消息(error, '创建标签失败'))
  }
}

async function 构建文章AI请求(): Promise<ArticleAIRequestPayload | null> {
  try {
    await loadEditorOptions()
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '加载分类和标签失败，无法生成 AI 请求'))
    return null
  }

  const content = (editorRef.value?.getMarkdown() ?? form.value.content).trim()
  if (!content) {
    ElMessage.warning('请先填写正文内容')
    return null
  }
  return {
    title: form.value.title,
    content,
    excerpt: form.value.excerpt,
    category_names: 已有分类名称列表.value,
    tag_names: 已有标签名称列表.value,
  }
}

function 打开AI辅助抽屉() {
  aiDrawerVisible.value = true
}

async function 生成AI元信息建议() {
  const payload = await 构建文章AI请求()
  if (!payload) {
    return
  }

  打开AI辅助抽屉()
  aiLoading.value = true
  aiStatusMessage.value = '正在生成元信息建议...'
  try {
    aiMetadataSuggestion.value = await 生成文章AI元信息建议(payload)
    aiStatusMessage.value = '元信息建议已生成，可选择应用。'
    ElMessage.success('AI 元信息建议已生成')
  } catch (error) {
    const message = 获取API错误消息(error, '生成 AI 元信息建议失败')
    aiStatusMessage.value = message
    ElMessage.error(message)
  } finally {
    aiLoading.value = false
  }
}

async function 生成AI润色正文() {
  const payload = await 构建文章AI请求()
  if (!payload) {
    return
  }

  打开AI辅助抽屉()
  aiLoading.value = true
  aiStatusMessage.value = '正在润色正文...'
  console.info('[ArticleAI] 开始润色正文', {
    contentLength: payload.content.length,
    title: payload.title || '',
  })
  try {
    const result = await AI润色文章正文(payload)
    console.info('[ArticleAI] 润色正文完成', {
      contentLength: result.content.length,
      summaryLength: result.summary.length,
    })
    aiPolishResult.value = result
    if (!result.content.trim()) {
      aiStatusMessage.value = 'AI 返回了空正文，请重试或缩短正文后再试。'
      ElMessage.warning(aiStatusMessage.value)
      return
    }
    aiStatusMessage.value = result.content.trim() === payload.content.trim()
      ? 'AI 已返回润色结果，但正文与当前内容基本一致。'
      : '正文润色结果已生成，可预览后替换。'
    ElMessage.success('AI 润色结果已生成')
  } catch (error) {
    const message = 获取API错误消息(error, 'AI 润色正文失败')
    console.error('[ArticleAI] 润色正文失败', error)
    aiStatusMessage.value = message
    ElMessage.error(message)
  } finally {
    aiLoading.value = false
  }
}

async function 确保分类存在(categoryName: string): Promise<string | null> {
  const normalizedName = categoryName.trim()
  if (!normalizedName) {
    return null
  }

  const existing = categories.value.find((item) => item.label === normalizedName)
  if (existing) {
    return existing.value
  }

  const category = await 创建分类(normalizedName)
  articleTaxonomyStore.upsertCategory(category)
  categories.value.push({ label: category.name, value: category.id })
  return category.id
}

async function 确保标签存在(tagName: string): Promise<string | null> {
  const normalizedName = tagName.trim()
  if (!normalizedName) {
    return null
  }

  const existing = tags.value.find((item) => item.label === normalizedName)
  if (existing) {
    return existing.value
  }

  const tag = await 创建标签(normalizedName)
  articleTaxonomyStore.upsertTag(tag)
  tags.value.push({ label: tag.name, value: tag.id })
  return tag.id
}

function 应用AI标题() {
  const title = aiMetadataSuggestion.value?.title.trim()
  if (!title) {
    return
  }
  form.value.title = title
}

function 应用AI摘要() {
  const excerpt = aiMetadataSuggestion.value?.excerpt.trim()
  if (!excerpt) {
    return
  }
  form.value.excerpt = excerpt
}

async function 应用AI分类() {
  const categoryName = aiMetadataSuggestion.value?.category_name?.trim()
  if (!categoryName) {
    return
  }

  try {
    const categoryId = await 确保分类存在(categoryName)
    if (categoryId) {
      form.value.category_id = categoryId
      ElMessage.success('已应用 AI 分类')
    }
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '应用 AI 分类失败'))
  }
}

async function 应用AI标签() {
  const suggestion = aiMetadataSuggestion.value
  if (!suggestion || suggestion.tag_names.length === 0) {
    return
  }

  try {
    const tagIds = await Promise.all(suggestion.tag_names.map((name) => 确保标签存在(name)))
    const mergedIds = new Set(form.value.tag_ids)
    for (const tagId of tagIds) {
      if (tagId) {
        mergedIds.add(tagId)
      }
    }
    form.value.tag_ids = [...mergedIds]
    ElMessage.success('已应用 AI 标签')
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '应用 AI 标签失败'))
  }
}

async function 应用AI全部元信息() {
  应用AI标题()
  应用AI摘要()
  await 应用AI分类()
  await 应用AI标签()
}

async function 替换为AI润色正文() {
  const polishedContent = aiPolishResult.value?.content
  if (!polishedContent) {
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定用 AI 润色结果替换当前正文？替换后仍需手动保存文章。',
      '替换正文',
      {
        type: 'warning',
        confirmButtonText: '替换',
        cancelButtonText: '取消',
      },
    )
    editorRef.value?.setMarkdown(polishedContent)
    form.value.content = polishedContent
    await nextTick()
    ElMessage.success('已替换为 AI 润色正文')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(获取API错误消息(error, '替换正文失败'))
    }
  }
}

function applyArticleToForm(article: ArticleRecord) {
  form.value = {
    title: article.title,
    content: article.content,
    excerpt: article.excerpt || '',
    cover_url: article.cover_url || '',
    status: article.status,
    category_id: article.category?.id || null,
    tag_ids: article.tags.map((tag) => tag.id),
  }
}

function buildEmptyForm(): ArticleEditorPayload {
  return {
    title: '',
    content: '',
    excerpt: '',
    cover_url: '',
    status: 'private',
    category_id: null,
    tag_ids: [],
  }
}

function cloneFormPayload(payload: ArticleEditorPayload): ArticleEditorPayload {
  return {
    ...payload,
    tag_ids: [...payload.tag_ids],
  }
}

function resetEditorForm() {
  form.value = buildEmptyForm()
}

function 清空文章图片状态() {
  articleImages.value = []
  selectedUnusedArticleImageIds.value = []
}

function 规范化站内文件路径(url: string | null | undefined): string | null {
  const trimmedUrl = url?.trim()
  if (!trimmedUrl) {
    return null
  }

  try {
    const parsedUrl = new window.URL(trimmedUrl, window.location.origin)
    if (!parsedUrl.pathname.startsWith('/files/')) {
      return null
    }
    return decodeURIComponent(parsedUrl.pathname)
  } catch {
    const [path] = trimmedUrl.split('?')
    if (!path?.startsWith('/files/')) {
      return null
    }
    return decodeURIComponent(path)
  }
}

function 收集已使用文章图片路径(content: string, coverUrl: string): Set<string> {
  const paths = new Set<string>()
  const normalizedCoverUrl = 规范化站内文件路径(coverUrl)
  if (normalizedCoverUrl) {
    paths.add(normalizedCoverUrl)
  }

  for (const match of content.matchAll(站内文件链接正则)) {
    const normalizedPath = 规范化站内文件路径(match[0])
    if (normalizedPath) {
      paths.add(normalizedPath)
    }
  }

  return paths
}

async function 同步文章图片(articleId: string) {
  const 当前加载序号 = ++文章图片加载序号

  if (!articleId) {
    articleImagesLoading.value = false
    清空文章图片状态()
    return
  }

  articleImagesLoading.value = true
  try {
    const images = await 获取文章图片(articleId)
    if (当前加载序号 !== 文章图片加载序号) {
      return
    }
    articleImages.value = images
  } catch (error) {
    if (当前加载序号 !== 文章图片加载序号) {
      return
    }

    清空文章图片状态()
    ElMessage.error(获取API错误消息(error, '加载文章图片失败'))
  } finally {
    if (当前加载序号 === 文章图片加载序号) {
      articleImagesLoading.value = false
    }
  }
}

async function syncArticleByRoute(articleId: string) {
  const 当前加载序号 = ++文章加载序号

  currentArticleId.value = articleId
  if (!articleId) {
    loading.value = false
    resetEditorForm()
    清空文章图片状态()
    markFormSaved()
    return
  }

  loading.value = true
  try {
    const article = await 根据ID获取我的文章(articleId)
    if (当前加载序号 !== 文章加载序号) {
      return
    }

    currentArticleId.value = article.id
    applyArticleToForm(article)
    await 同步文章图片(article.id)
    markFormSaved()
  } catch (error) {
    if (当前加载序号 !== 文章加载序号) {
      return
    }

    currentArticleId.value = ''
    resetEditorForm()
    清空文章图片状态()
    markFormSaved()
    ElMessage.error(获取API错误消息(error, '加载文章失败'))
  } finally {
    if (当前加载序号 === 文章加载序号) {
      loading.value = false
    }
  }
}

async function syncEditorStateFromRoute(force = false) {
  const routeArticleId = getRouteArticleId()
  if (!force && routeArticleId === currentArticleId.value) {
    return
  }

  await syncArticleByRoute(routeArticleId)
}

onMounted(() => {
  previewType.value = 'preview'
  previewLayoutMode.value = isMobileViewport.value ? 'hidden' : 'split'

  void loadEditorOptions().catch((error) => {
    ElMessage.error(获取API错误消息(error, '加载分类和标签失败'))
  })
  void syncEditorStateFromRoute(true)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  编辑器尺寸观察器?.disconnect()
  if (滚动同步初始化帧) {
    window.cancelAnimationFrame(滚动同步初始化帧)
    滚动同步初始化帧 = 0
  }
  清理滚动同步监听()
})

watch(
  () => editorRef.value,
  async () => {
    await nextTick()
    初始化编辑器内容区尺寸观察()
  },
  { flush: 'post' },
)

watch(
  isMobileViewport,
  async () => {
    await nextTick()
    初始化编辑器内容区尺寸观察()
  },
  { flush: 'post' },
)

watch([previewType, previewLayoutMode, scrollSyncEnabled], async () => {
  await 调度滚动同步监听初始化()
})

watch(
  () => editorRef.value,
  async () => {
    await 调度滚动同步监听初始化()
  },
  { flush: 'post' },
)

watch(
  () => form.value.content,
  async () => {
    await nextTick()
    将编辑器滚动同步到预览()
  },
  { flush: 'post' },
)

watch(
  () => getRouteArticleId(),
  (routeArticleId, previousRouteArticleId) => {
    if (routeArticleId === previousRouteArticleId) {
      return
    }
    void syncEditorStateFromRoute()
  },
)

onBeforeRouteLeave(async () => {
  if (saving.value || formatting.value || isUploadingImages.value) {
    ElMessage.warning(
      isUploadingImages.value
        ? '图片仍在上传，请稍后'
        : (formatting.value ? '正在美化内容，请稍后' : '正在保存，请稍后'),
    )
    return false
  }

  if (!isDirty.value) {
    return true
  }

  try {
    await ElMessageBox.confirm(
      '当前文章有未保存内容，是否先保存再退出？',
      '未保存内容',
      {
        confirmButtonText: '保存并退出',
        cancelButtonText: '直接退出',
        distinguishCancelAndClose: true,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        type: 'warning',
      },
    )
    return await saveArticle({ redirectAfterSave: false, syncRouteAfterSave: false })
  } catch (action: unknown) {
    return action === 'cancel'
  }
})

function buildFormSnapshot(payload: ArticleEditorPayload): string {
  return JSON.stringify({
    ...payload,
    category_id: payload.category_id ?? null,
    tag_ids: [...payload.tag_ids].sort(),
  })
}

function markFormSaved() {
  savedForm.value = cloneFormPayload(form.value)
}

function isSameTagIds(currentTagIds: string[], previousTagIds: string[]): boolean {
  return JSON.stringify([...currentTagIds].sort()) === JSON.stringify([...previousTagIds].sort())
}

function buildUpdatePayload(currentPayload: ArticleEditorPayload, previousPayload: ArticleEditorPayload): ArticleUpdatePayload {
  const payload: ArticleUpdatePayload = {}

  if (currentPayload.title !== previousPayload.title) {
    payload.title = currentPayload.title
  }
  if (currentPayload.content !== previousPayload.content) {
    payload.content = currentPayload.content
  }
  if (currentPayload.excerpt !== previousPayload.excerpt) {
    payload.excerpt = currentPayload.excerpt
  }
  if (currentPayload.cover_url !== previousPayload.cover_url) {
    payload.cover_url = currentPayload.cover_url
  }
  if (currentPayload.status !== previousPayload.status) {
    payload.status = currentPayload.status
  }
  if (currentPayload.category_id !== previousPayload.category_id) {
    payload.category_id = currentPayload.category_id
  }
  if (!isSameTagIds(currentPayload.tag_ids, previousPayload.tag_ids)) {
    payload.tag_ids = [...currentPayload.tag_ids]
  }

  return payload
}

function 尝试从内容补全标题() {
  if (form.value.title.trim()) {
    return
  }

  const extractedTitle = 从Markdown首行提取文章标题(form.value.content)
  if (!extractedTitle) {
    return
  }

  form.value.title = extractedTitle
}

function buildDraftPayload(): ArticleDraftPayload {
  尝试从内容补全标题()
  return {
    title: form.value.title,
    content: form.value.content,
    excerpt: form.value.excerpt,
    cover_url: form.value.cover_url,
    category_id: form.value.category_id,
    tag_ids: [...form.value.tag_ids],
  }
}

async function createCurrentArticle() {
  尝试从内容补全标题()
  const created = await 创建文章(form.value)
  currentArticleId.value = created.id
  return created.id
}

async function updateCurrentArticle() {
  if (!currentArticleId.value) {
    throw new Error('missing_article_id')
  }

  尝试从内容补全标题()
  const payload = buildUpdatePayload(form.value, savedForm.value)
  await 更新文章(currentArticleId.value, payload)
  return currentArticleId.value
}

async function syncEditorRoute(articleId: string) {
  if (!articleId) {
    return
  }
  if (!['DesktopArticleEditor', 'ArticleEditor'].includes(String(route.name ?? '')) || getRouteArticleId() === articleId) {
    return
  }

  await router.replace({
    name: String(route.name ?? '') === 'ArticleEditor' ? 'ArticleEditor' : 'DesktopArticleEditor',
    params: { id: articleId },
  })
}

async function ensureDraftArticleForImageUpload(): Promise<string> {
  if (currentArticleId.value) {
    return currentArticleId.value
  }

  const draft = await 创建文章草稿(buildDraftPayload())
  currentArticleId.value = draft.id
  await syncEditorRoute(draft.id)
  return draft.id
}

function 同步编辑器内容区尺寸() {
  const 编辑器容器 = editorWrapperRef.value
  if (!编辑器容器) {
    return
  }

  const 内容区元素 = 编辑器容器.querySelector('.milkdown-markdown-editor__content')
  if (内容区元素 instanceof globalThis.HTMLElement) {
    const 容器矩形 = 编辑器容器.getBoundingClientRect()
    const 内容区矩形 = 内容区元素.getBoundingClientRect()

    编辑器内容区顶部偏移.value = Math.max(0, 内容区矩形.top - 容器矩形.top)
    编辑器内容区底部偏移.value = Math.max(0, 容器矩形.bottom - 内容区矩形.bottom)
    return
  }

  const 工具栏元素 = 编辑器容器.querySelector('.milkdown-markdown-editor__toolbar')
  const 页脚元素 = 编辑器容器.querySelector('.milkdown-markdown-editor__footer')

  编辑器内容区顶部偏移.value = 工具栏元素 instanceof globalThis.HTMLElement ? 工具栏元素.offsetHeight : 0
  编辑器内容区底部偏移.value = 页脚元素 instanceof globalThis.HTMLElement ? 页脚元素.offsetHeight : 0
}

function 初始化编辑器内容区尺寸观察() {
  编辑器尺寸观察器?.disconnect()
  编辑器尺寸观察器 = null

  const 编辑器容器 = editorWrapperRef.value
  if (!编辑器容器) {
    return
  }

  同步编辑器内容区尺寸()

  if (typeof window.ResizeObserver === 'undefined') {
    return
  }

  编辑器尺寸观察器 = new window.ResizeObserver(() => {
    同步编辑器内容区尺寸()
  })
  编辑器尺寸观察器.observe(编辑器容器)

  const 工具栏元素 = 编辑器容器.querySelector('.milkdown-markdown-editor__toolbar')
  const 内容区元素 = 编辑器容器.querySelector('.milkdown-markdown-editor__content')
  const 页脚元素 = 编辑器容器.querySelector('.milkdown-markdown-editor__footer')

  if (工具栏元素 instanceof globalThis.HTMLElement) {
    编辑器尺寸观察器.observe(工具栏元素)
  }
  if (内容区元素 instanceof globalThis.HTMLElement) {
    编辑器尺寸观察器.observe(内容区元素)
  }
  if (页脚元素 instanceof globalThis.HTMLElement) {
    编辑器尺寸观察器.observe(页脚元素)
  }
}

function 获取预览滚动容器(): globalThis.HTMLElement | null {
  if (isMarkdownSplitVisible.value) {
    return markdownOverlayRef.value
  }

  if (isHtmlSplitVisible.value) {
    return htmlOverlayRef.value
  }

  return null
}

function 获取滚动比例(元素: globalThis.HTMLElement): number {
  const 最大滚动距离 = 元素.scrollHeight - 元素.clientHeight
  if (最大滚动距离 <= 0) {
    return 0
  }

  return 元素.scrollTop / 最大滚动距离
}

function 设置滚动比例(元素: globalThis.HTMLElement, 滚动比例: number) {
  const 最大滚动距离 = 元素.scrollHeight - 元素.clientHeight
  const 规范比例 = Math.min(1, Math.max(0, 滚动比例))
  元素.scrollTop = 最大滚动距离 <= 0 ? 0 : 最大滚动距离 * 规范比例
}

function 清理滚动同步监听() {
  for (const 清理 of 滚动同步清理列表) {
    清理()
  }

  滚动同步清理列表 = []
  当前滚动同步来源 = null
  if (滚动同步帧) {
    window.cancelAnimationFrame(滚动同步帧)
    滚动同步帧 = 0
  }
}

function 初始化滚动同步监听() {
  if (滚动同步初始化帧) {
    window.cancelAnimationFrame(滚动同步初始化帧)
    滚动同步初始化帧 = 0
  }

  清理滚动同步监听()

  if (!scrollSyncEnabled.value) {
    return
  }

  const 编辑器实例 = editorRef.value
  const 编辑器滚动容器 = 编辑器实例?.getScrollElement()
  const 预览滚动容器 = 获取预览滚动容器()

  if (!编辑器实例 || !编辑器滚动容器 || !预览滚动容器) {
    return
  }

  const 同步到预览 = () => {
    if (当前滚动同步来源 === 'preview') {
      return
    }

    当前滚动同步来源 = 'editor'
    window.cancelAnimationFrame(滚动同步帧)
    滚动同步帧 = window.requestAnimationFrame(() => {
      设置滚动比例(预览滚动容器, 编辑器实例.getScrollRatio())
      当前滚动同步来源 = null
      滚动同步帧 = 0
    })
  }

  const 同步到编辑器 = () => {
    if (当前滚动同步来源 === 'editor') {
      return
    }

    当前滚动同步来源 = 'preview'
    window.cancelAnimationFrame(滚动同步帧)
    滚动同步帧 = window.requestAnimationFrame(() => {
      编辑器实例.setScrollRatio(获取滚动比例(预览滚动容器))
      当前滚动同步来源 = null
      滚动同步帧 = 0
    })
  }

  编辑器滚动容器.addEventListener('scroll', 同步到预览, { passive: true })
  预览滚动容器.addEventListener('scroll', 同步到编辑器, { passive: true })
  滚动同步清理列表 = [
    () => 编辑器滚动容器.removeEventListener('scroll', 同步到预览),
    () => 预览滚动容器.removeEventListener('scroll', 同步到编辑器),
  ]

  将编辑器滚动同步到预览()
}

async function 调度滚动同步监听初始化() {
  await nextTick()
  if (滚动同步初始化帧) {
    window.cancelAnimationFrame(滚动同步初始化帧)
  }

  滚动同步初始化帧 = window.requestAnimationFrame(() => {
    滚动同步初始化帧 = 0
    初始化编辑器内容区尺寸观察()
    初始化滚动同步监听()
  })
}

function handleEditorReady() {
  void 调度滚动同步监听初始化()
}

function 将编辑器滚动同步到预览() {
  if (!scrollSyncEnabled.value) {
    return
  }

  const 编辑器实例 = editorRef.value
  const 预览滚动容器 = 获取预览滚动容器()
  if (!编辑器实例 || !预览滚动容器) {
    return
  }

  设置滚动比例(预览滚动容器, 编辑器实例.getScrollRatio())
}

function handleBeforeUnload(event: globalThis.BeforeUnloadEvent) {
  if (!isDirty.value && !isUploadingImages.value) {
    return
  }

  event.preventDefault()
  event.returnValue = ''
}

function 转义Markdown图片说明文本(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/\[/g, '\\[')
    .replace(/\]/g, '\\]')
    .replace(/\r?\n/g, ' ')
    .trim()
}

function 提取图片说明文件名(value: string): string {
  const trimmedValue = value.trim()
  const lastDotIndex = trimmedValue.lastIndexOf('.')
  if (lastDotIndex > 0) {
    return trimmedValue.slice(0, lastDotIndex)
  }
  return trimmedValue
}

async function handleEditorImageUpload(files: File[]): Promise<MilkdownMarkdownImagePayload[]> {
  if (files.length === 0) {
    return []
  }

  uploadingImageCount.value += 1

  try {
    const articleId = await ensureDraftArticleForImageUpload()
    const uploadedFiles = await Promise.all(files.map((file) => 上传文章图片(articleId, file)))
    await 同步文章图片(articleId)
    return uploadedFiles.map((file) => ({
      url: file.url,
      alt: 转义Markdown图片说明文本(提取图片说明文件名(file.original_name)),
      title: '',
    }))
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '图片上传失败'))
    throw error
  } finally {
    uploadingImageCount.value = Math.max(0, uploadingImageCount.value - 1)
  }
}

function getMarkdownPrettier(): MarkdownPrettierContext | null {
  const markdownWindow = window as MarkdownPrettierWindow
  const markdownPlugin = markdownWindow.prettierPlugins?.markdown

  if (!markdownWindow.prettier || !markdownPlugin) {
    return null
  }

  return {
    prettier: markdownWindow.prettier,
    markdownPlugin,
  }
}

async function waitForMarkdownPrettier(timeoutMs = 5000): Promise<MarkdownPrettierContext | null> {
  const startTime = Date.now()
  let prettierContext = getMarkdownPrettier()

  while (!prettierContext && Date.now() - startTime < timeoutMs) {
    await new Promise((resolve) => window.setTimeout(resolve, 50))
    prettierContext = getMarkdownPrettier()
  }

  return prettierContext
}

async function formatArticleContent(): Promise<boolean> {
  const prettierContext = await waitForMarkdownPrettier()
  if (!prettierContext) {
    ElMessage.error('编辑器美化组件尚未就绪，请稍后再试')
    return false
  }

  const currentContent = editorRef.value?.getMarkdown() ?? form.value.content

  formatting.value = true
  try {
    const formattedContent = await prettierContext.prettier.format(currentContent, {
      parser: 'markdown',
      plugins: [prettierContext.markdownPlugin],
    })

    if (formattedContent === currentContent) {
      return true
    }

    editorRef.value?.setMarkdown(formattedContent)
    form.value.content = formattedContent
    await nextTick()
    return true
  } catch (error) {
    ElMessage.error(获取API错误消息(error, '美化失败'))
    return false
  } finally {
    formatting.value = false
  }
}

async function formatAndSaveArticle(): Promise<boolean> {
  if (!await formatArticleContent()) {
    return false
  }

  if (!isDirty.value) {
    ElMessage.info('没有可保存的更改')
    return false
  }

  return saveArticle({ redirectAfterSave: false, syncRouteAfterSave: true })
}

async function saveArticle(options: SaveArticleOptions): Promise<boolean> {
  尝试从内容补全标题()

  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return false
  }
  if (isUploadingImages.value) {
    ElMessage.warning('图片仍在上传，请稍后')
    return false
  }

  let savedArticleId: string

  saving.value = true
  try {
    if (isEdit.value) {
      savedArticleId = await updateCurrentArticle()
      ElMessage.success('更新成功')
    } else {
      savedArticleId = await createCurrentArticle()
      ElMessage.success('创建成功')
    }
    markFormSaved()
  } catch (error) {
    if (error instanceof Error && error.message === 'missing_article_id') {
      ElMessage.error('缺少文章 ID，无法更新')
      return false
    }
    ElMessage.error(获取API错误消息(error, '保存失败'))
    return false
  } finally {
    saving.value = false
  }

  if (options.redirectAfterSave) {
    await router.push(`${路由前缀.value}/articles`)
    return true
  }

  if (options.syncRouteAfterSave !== false) {
    await syncEditorRoute(savedArticleId)
  }

  return true
}

async function save() {
  await saveArticle({ redirectAfterSave: true, syncRouteAfterSave: false })
}

watch(未使用文章图片列表, (unusedImages) => {
  const unusedIds = new Set(unusedImages.map((image) => image.id))
  selectedUnusedArticleImageIds.value = selectedUnusedArticleImageIds.value.filter((id) => unusedIds.has(id))
}, { immediate: true })

function 切换未使用文章图片选择(imageId: string, checked: boolean) {
  if (checked) {
    if (!selectedUnusedArticleImageIds.value.includes(imageId)) {
      selectedUnusedArticleImageIds.value = [...selectedUnusedArticleImageIds.value, imageId]
    }
    return
  }

  selectedUnusedArticleImageIds.value = selectedUnusedArticleImageIds.value.filter((id) => id !== imageId)
}

function 选中全部未使用文章图片() {
  selectedUnusedArticleImageIds.value = 未使用文章图片列表.value.map((image) => image.id)
}

function 清空未使用文章图片选择() {
  selectedUnusedArticleImageIds.value = []
}

function 切换文章图片面板展开状态() {
  articleImagePanelExpanded.value = !articleImagePanelExpanded.value
}

function 获取文章图片预览地址(image: ArticleImageRecord): string {
  return 解析管理文件URL地址(image.thumbnail_url || image.preview_url || image.url)
}

function 格式化文章图片大小(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function 格式化文章图片时间(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

async function 删除选中未使用文章图片() {
  if (selectedUnusedArticleImageIds.value.length === 0) {
    return
  }

  await ElMessageBox.confirm(
    `确定删除选中的 ${selectedUnusedArticleImageIds.value.length} 张未使用图片？删除后无法恢复。`,
    '删除未使用图片',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    },
  )

  deletingArticleImages.value = true
  try {
    const 选中ID集合 = new Set(selectedUnusedArticleImageIds.value)
    const 删除结果 = await Promise.allSettled(
      selectedUnusedArticleImageIds.value.map((imageId) => 删除管理文件(imageId)),
    )
    const 删除成功数量 = 删除结果.filter((item) => item.status === 'fulfilled').length
    const 删除失败数量 = 删除结果.length - 删除成功数量

    if (删除成功数量 > 0) {
      articleImages.value = articleImages.value.filter((image) => !选中ID集合.has(image.id))
      清空未使用文章图片选择()
    }

    if (删除失败数量 === 0) {
      ElMessage.success(`已删除 ${删除成功数量} 张未使用图片`)
      return
    }

    ElMessage.warning(`成功删除 ${删除成功数量} 张，另有 ${删除失败数量} 张删除失败`)
    await 同步文章图片(currentArticleId.value)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(获取API错误消息(error, '删除文章图片失败'))
    }
  } finally {
    deletingArticleImages.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <PageSectionShell
      :title="isEdit ? '编辑文章' : '写文章'"
      :icon="isEdit ? EditPen : DocumentAdd"
      title-tag="h2"
      :show-back="props.showBack"
      :to="props.backTo"
    >
      <ElSkeleton :loading="loading" animated>
        <ElForm label-position="top">
        <ElFormItem label="标题">
          <ElInput v-model="form.title" placeholder="文章标题" />
        </ElFormItem>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
          <ElFormItem>
            <template #label>
              <div style="display: flex; align-items: center; gap: 8px">
                <span>分类</span>
                <ElButton link type="primary" size="small" @click="handleCreateCategory">+ 新增</ElButton>
              </div>
            </template>
            <ElSelect v-model="form.category_id" placeholder="选择分类" clearable>
              <ElOption v-for="item in categories" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem>
            <template #label>
              <div style="display: flex; align-items: center; gap: 8px">
                <span>标签</span>
                <ElButton link type="primary" size="small" @click="handleCreateTag">+ 新增</ElButton>
              </div>
            </template>
            <ElSelect v-model="form.tag_ids" placeholder="选择标签" multiple clearable>
              <ElOption v-for="item in tags" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
        </div>

        <ElFormItem label="封面图 URL">
          <ElInput v-model="form.cover_url" placeholder="https://..." />
        </ElFormItem>

        <ElFormItem label="摘要">
          <ElInput v-model="form.excerpt" type="textarea" placeholder="文章摘要（可选）" :rows="2" />
        </ElFormItem>

        <ElFormItem class="editor-form-item">
          <template #label>
            <div class="editor-form-item__label">
              <span>正文 (Markdown)</span>
              <div class="editor-form-item__controls">
                <ElButton
                  plain
                  size="small"
                  :icon="MagicStick"
                  :loading="aiLoading"
                  @click="生成AI元信息建议"
                >
                  生成元信息
                </ElButton>
                <ElButton
                  plain
                  size="small"
                  :icon="MagicStick"
                  :loading="aiLoading"
                  @click="生成AI润色正文"
                >
                  润色正文
                </ElButton>
                <SegmentedSwitch
                  v-model="previewType"
                  aria-label="文章预览类型"
                  :options="previewTypeOptions"
                  active-color="var(--el-color-primary)"
                  size="small"
                />
                <SegmentedSwitch
                  v-model="previewLayoutMode"
                  aria-label="文章预览显示方式"
                  :options="previewLayoutModeOptions"
                  active-color="var(--el-color-primary)"
                  size="small"
                />
              </div>
            </div>
          </template>
          <div class="editor-workspace">
            <div
              ref="editorWrapperRef"
              class="editor-wrapper"
              :class="{
                'editor-wrapper--markdown-split': isMarkdownSplitVisible,
                'editor-wrapper--markdown-full': isMarkdownFullVisible,
                'editor-wrapper--html-split': isHtmlSplitVisible,
                'editor-wrapper--html-full': isHtmlFullVisible,
                'editor-wrapper--mindmap-split': isMindmapSplitVisible,
                'editor-wrapper--mindmap-full': isMindmapFullVisible,
              }"
              :style="编辑器内容区覆盖样式"
            >
              <MilkdownMarkdownEditor
                :id="editorId"
                ref="editorRef"
                v-model="form.content"
                class="article-milkdown-editor"
                :theme="editorTheme"
                placeholder="在此编写 Markdown 内容..."
                :upload-images="handleEditorImageUpload"
                :format-content="formatArticleContent"
                v-model:scroll-sync="scrollSyncEnabled"
                :show-scroll-sync="previewLayoutMode === 'split'"
                fullscreen-root-selector=".editor-wrapper"
                @ready="handleEditorReady"
                @upload-error="(error) => ElMessage.error(获取API错误消息(error, '图片上传失败'))"
                @mode-change="调度滚动同步监听初始化"
              />

              <div v-if="isMarkdownPreviewVisible" ref="markdownOverlayRef" class="markdown-editor-overlay">
                <MarkdownRenderer
                  class="markdown-editor-overlay__content article-markdown-preview"
                  :content="form.content"
                  :debounce-ms="180"
                />
              </div>

              <div v-if="isHtmlPreviewVisible" ref="htmlOverlayRef" class="html-editor-overlay">
                <pre class="html-editor-overlay__content"><code>{{ htmlPreviewContent }}</code></pre>
              </div>

              <div v-if="isMindmapPreviewVisible" class="mindmap-editor-overlay">
                <MarkdownMindmap
                  :content="form.content"
                  :title="form.title"
                  height="100%"
                />
              </div>
            </div>
          </div>
        </ElFormItem>

        <ArticleImagePanel
          :expanded="articleImagePanelExpanded"
          :current-article-id="currentArticleId"
          :loading="articleImagesLoading"
          :deleting="deletingArticleImages"
          :items="文章图片列表项"
          :desktop-summary="文章图片桌面摘要"
          :mobile-summary="文章图片移动端摘要"
          :selected-ids="selectedUnusedArticleImageIds"
          :unused-count="未使用文章图片列表.length"
          :resolve-preview-url="获取文章图片预览地址"
          :format-size="格式化文章图片大小"
          :format-time="格式化文章图片时间"
          @toggle="切换文章图片面板展开状态"
          @refresh="同步文章图片(currentArticleId)"
          @select-all-unused="选中全部未使用文章图片"
          @clear-selection="清空未使用文章图片选择"
          @delete-selected="删除选中未使用文章图片"
          @selection-change="切换未使用文章图片选择"
        />

          <div class="article-editor-actions">
            <ElFormItem label="状态" class="article-editor-status">
              <SegmentedSwitch
                v-model="form.status"
                aria-label="文章状态"
                :options="articleStatusOptions"
                active-color="var(--el-color-primary)"
              />
            </ElFormItem>

            <div class="article-editor-buttons">
              <ElButton type="primary" :loading="saving || formatting || isUploadingImages" @click="save">
                {{ isEdit ? '更新' : '创建' }}
              </ElButton>
              <ElButton @click="router.back()">取消</ElButton>
            </div>
          </div>
        </ElForm>
      </ElSkeleton>
    </PageSectionShell>

    <ElDrawer
      v-model="aiDrawerVisible"
      title="AI 辅助"
      size="520px"
      class="article-ai-drawer"
    >
      <div class="article-ai-panel">
        <div class="article-ai-panel__actions">
          <ElButton plain :icon="MagicStick" :loading="aiLoading" @click="生成AI元信息建议">
            生成元信息
          </ElButton>
          <ElButton plain :icon="MagicStick" :loading="aiLoading" @click="生成AI润色正文">
            润色正文
          </ElButton>
        </div>

        <div v-if="aiStatusMessage" class="article-ai-status">
          {{ aiStatusMessage }}
        </div>

        <section v-if="aiMetadataSuggestion" class="article-ai-section">
          <div class="article-ai-section__header">
            <h3>元信息建议</h3>
            <ElButton type="primary" plain size="small" @click="应用AI全部元信息">全部应用</ElButton>
          </div>

          <div class="article-ai-field">
            <div class="article-ai-field__label">
              <span>标题</span>
              <ElButton link type="primary" size="small" @click="应用AI标题">应用</ElButton>
            </div>
            <p>{{ aiMetadataSuggestion.title }}</p>
          </div>

          <div class="article-ai-field">
            <div class="article-ai-field__label">
              <span>摘要</span>
              <ElButton link type="primary" size="small" @click="应用AI摘要">应用</ElButton>
            </div>
            <p>{{ aiMetadataSuggestion.excerpt }}</p>
          </div>

          <div class="article-ai-field">
            <div class="article-ai-field__label">
              <span>分类</span>
              <ElButton link type="primary" size="small" @click="应用AI分类">应用</ElButton>
            </div>
            <ElSpace wrap>
              <ElTag v-if="aiMetadataSuggestion.category_name" effect="plain">
                {{ aiMetadataSuggestion.category_name }}
              </ElTag>
              <ElTag v-if="aiMetadataSuggestion.category_name && !AI建议分类已存在" type="warning" effect="plain">
                将新建
              </ElTag>
              <span v-if="!aiMetadataSuggestion.category_name" class="article-ai-muted">未建议分类</span>
            </ElSpace>
          </div>

          <div class="article-ai-field">
            <div class="article-ai-field__label">
              <span>标签</span>
              <ElButton link type="primary" size="small" @click="应用AI标签">应用</ElButton>
            </div>
            <ElSpace wrap>
              <ElTag v-for="tagName in aiMetadataSuggestion.tag_names" :key="tagName" effect="plain">
                {{ tagName }}
              </ElTag>
              <ElTag v-if="AI建议新标签列表.length > 0" type="warning" effect="plain">
                {{ AI建议新标签列表.length }} 个将新建
              </ElTag>
            </ElSpace>
          </div>

          <div v-if="aiMetadataSuggestion.reason" class="article-ai-field">
            <div class="article-ai-field__label">
              <span>依据</span>
            </div>
            <p>{{ aiMetadataSuggestion.reason }}</p>
          </div>
        </section>

        <section v-if="aiPolishResult" class="article-ai-section">
          <div class="article-ai-section__header">
            <h3>正文润色</h3>
            <ElButton type="primary" plain size="small" @click="替换为AI润色正文">替换正文</ElButton>
          </div>
          <p v-if="aiPolishResult.summary" class="article-ai-summary">{{ aiPolishResult.summary }}</p>
          <pre class="article-ai-content-preview">{{ aiPolishResult.content }}</pre>
        </section>

        <div v-if="!aiMetadataSuggestion && !aiPolishResult" class="article-ai-empty">
          生成结果会显示在这里。
        </div>
      </div>
    </ElDrawer>
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

.page-container :deep(.page-header-shell__header) {
  margin-bottom: 24px;
}

.editor-form-item:deep(.el-form-item__label) {
  width: 100%;
  padding-bottom: 12px;
}

.editor-form-item:deep(.el-form-item__content) {
  display: block;
  width: 100%;
  line-height: normal;
}

.editor-form-item__label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.editor-form-item__controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.editor-workspace {
  display: block;
  width: 100%;
  min-width: 0;
}

.editor-wrapper {
  --article-editor-panel-bg: var(--card-bg-transparent, var(--el-bg-color-overlay));
  --article-editor-panel-bg-color: rgba(255, 255, 255, var(--overlay-card-opacity, 0.68));
  --milkdown-markdown-editor-bg: var(--article-editor-panel-bg);
  --milkdown-markdown-editor-bg-color: var(--article-editor-panel-bg-color);
  --milkdown-markdown-editor-toolbar-bg: var(--article-editor-panel-bg);
  --milkdown-markdown-editor-toolbar-bg-color: var(--article-editor-panel-bg-color);
  --milkdown-markdown-editor-content-bg: var(--article-editor-panel-bg);
  --milkdown-markdown-editor-content-bg-color: var(--article-editor-panel-bg-color);
  position: relative;
  width: 100%;
  min-width: 0;
  border-radius: 12px;
  overflow: hidden;
  background: var(--article-editor-panel-bg);
  background-color: var(--article-editor-panel-bg-color);
}

.dark .editor-wrapper {
  --article-editor-panel-bg-color: rgba(15, 23, 42, var(--overlay-card-opacity, 0.62));
}

.editor-wrapper.milkdown-markdown-editor--page-fullscreen,
.editor-wrapper:fullscreen {
  --article-editor-panel-bg: var(--el-bg-color);
  --article-editor-panel-bg-color: var(--el-bg-color);
  --milkdown-markdown-editor-bg: var(--el-bg-color);
  --milkdown-markdown-editor-bg-color: var(--el-bg-color);
  --milkdown-markdown-editor-toolbar-bg: var(--el-bg-color-overlay);
  --milkdown-markdown-editor-toolbar-bg-color: var(--el-bg-color-overlay);
  --milkdown-markdown-editor-content-bg: var(--el-bg-color);
  --milkdown-markdown-editor-content-bg-color: var(--el-bg-color);
  position: fixed;
  inset: 0;
  z-index: 3000;
  width: 100vw !important;
  height: 100dvh !important;
  border-radius: 0;
  background: var(--el-bg-color);
  background-color: var(--el-bg-color);
}

.editor-wrapper:fullscreen {
  position: fixed;
}

.editor-wrapper.milkdown-markdown-editor--page-fullscreen :deep(.milkdown-markdown-editor),
.editor-wrapper:fullscreen :deep(.milkdown-markdown-editor) {
  width: 100% !important;
  height: 100% !important;
  border-radius: 0;
  background: var(--el-bg-color);
  background-color: var(--el-bg-color);
}

.editor-wrapper--markdown-split :deep(.milkdown-markdown-editor__content),
.editor-wrapper--html-split :deep(.milkdown-markdown-editor__content),
.editor-wrapper--mindmap-split :deep(.milkdown-markdown-editor__content) {
  width: 50% !important;
  max-width: 50%;
}

.editor-wrapper--markdown-split :deep(.milkdown-markdown-editor),
.editor-wrapper--html-split :deep(.milkdown-markdown-editor),
.editor-wrapper--mindmap-split :deep(.milkdown-markdown-editor) {
  background: var(--article-editor-panel-bg);
  background-color: var(--article-editor-panel-bg-color);
}

.editor-wrapper--markdown-full :deep(.milkdown-markdown-editor__content),
.editor-wrapper--html-full :deep(.milkdown-markdown-editor__content),
.editor-wrapper--mindmap-full :deep(.milkdown-markdown-editor__content) {
  visibility: hidden;
  pointer-events: none;
}

.markdown-editor-overlay,
.html-editor-overlay,
.mindmap-editor-overlay {
  position: absolute;
  inset:
    var(--editor-content-top-offset, 0px)
    0
    var(--editor-content-bottom-offset, 24px)
    0;
  z-index: 2;
}

.markdown-editor-overlay {
  overflow: auto;
  background: var(--article-editor-panel-bg);
  background-color: var(--article-editor-panel-bg-color);
}

.editor-wrapper--markdown-split .markdown-editor-overlay,
.editor-wrapper--html-split .html-editor-overlay,
.editor-wrapper--mindmap-split .mindmap-editor-overlay {
  left: 50%;
  border-left: 1px solid color-mix(in srgb, var(--el-border-color) 88%, var(--el-text-color-secondary));
  box-shadow: inset 1px 0 0 color-mix(in srgb, var(--article-editor-panel-bg-color) 70%, transparent);
}

.markdown-editor-overlay__content {
  min-height: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
}

.html-editor-overlay {
  overflow: auto;
  background: var(--article-editor-panel-bg);
  background-color: var(--article-editor-panel-bg-color);
}

.html-editor-overlay__content {
  min-height: 100%;
  margin: 0;
  padding: 20px 24px;
  box-sizing: border-box;
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.mindmap-editor-overlay :deep(.markdown-mindmap) {
  min-height: 100%;
  height: 100%;
  border: none;
  border-radius: 0;
}

.article-milkdown-editor {
  width: 100%;
  height: 720px;
}

.article-editor-actions {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.article-editor-status {
  margin-bottom: 0;
}

.article-editor-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.article-ai-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.article-ai-panel__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.article-ai-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.article-ai-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.article-ai-section__header h3 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.article-ai-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.article-ai-field__label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.article-ai-field p,
.article-ai-summary {
  margin: 0;
  color: var(--el-text-color-primary);
  line-height: 1.7;
}

.article-ai-muted,
.article-ai-empty {
  color: var(--el-text-color-secondary);
}

.article-ai-status {
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.article-ai-empty {
  padding: 32px 0;
  text-align: center;
}

.article-ai-content-preview {
  max-height: 420px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

@media (--mobile-viewport) {
  .page-container {
    padding: 16px;
  }

  .editor-form-item__label {
    align-items: flex-start;
    flex-direction: column;
  }

  .editor-form-item__controls {
    width: 100%;
    align-items: stretch;
  }

  .markdown-editor-overlay__content,
  .html-editor-overlay__content {
    padding: 16px;
  }

  .article-milkdown-editor {
    height: 560px;
  }

  .article-editor-actions {
    align-items: stretch;
  }

  .article-editor-buttons {
    width: 100%;
    justify-content: flex-end;
  }

  .article-ai-panel__actions {
    align-items: stretch;
    flex-direction: column;
  }

  .article-ai-panel__actions :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }
}
</style>
