<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import {
  ElButton,
  ElCheckbox,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
  ElSkeleton,
  ElTag,
} from 'element-plus'
import { Connection, Document, DocumentAdd, EditPen, View } from '@element-plus/icons-vue'
import type { ExposeParam, UploadImgEvent } from 'md-editor-v3'
import MarkdownRenderer from '../../components/MarkdownRenderer.vue'
import SegmentedSwitch from '../../components/SegmentedSwitch.vue'
import { useEditorShortcuts } from '../../composables/useEditorShortcuts'
import { useSaveShortcut } from '../../composables/useSaveShortcut'
import { useViewport } from '../../composables/useViewport'
import {
  createArticle,
  createArticleDraft,
  createCategory,
  createTag,
  fetchArticleImages,
  fetchCategories,
  fetchMyArticleById,
  fetchTags,
  uploadArticleImage,
  updateArticle,
} from '../../features/articles/api'
import type {
  ArticleDraftPayload,
  ArticleEditorPayload,
  ArticleImageRecord,
  ArticleRecord,
  ArticleUpdatePayload,
} from '../../features/articles/types'
import { deleteFile as deleteManagedFile } from '../../features/files/api'
import { useThemeStore } from '../../stores/theme'
import { getApiErrorMessage } from '../../utils/api'
import { resolveManagedFileUrl } from '../../utils/managedFile'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()

const editorCoreLoading = ref(true)
const MdEditor = defineAsyncComponent({
  loader: async () => {
    try {
      const [editorModule] = await Promise.all([
        import('md-editor-v3'),
        import('md-editor-v3/lib/style.css'),
      ])
      return editorModule.MdEditor
    } finally {
      editorCoreLoading.value = false
    }
  },
  delay: 0,
  suspensible: false,
})
const MarkdownMindmap = defineAsyncComponent(() => import('../../components/MarkdownMindmap.vue'))

const currentArticleId = ref('')
const isEdit = computed(() => currentArticleId.value.length > 0)
const loading = ref(false)
const saving = ref(false)
const formatting = ref(false)
const uploadingImageCount = ref(0)
const editorId = 'article-editor'
const editorRef = ref<ExposeParam>()
const editorWrapperRef = ref<globalThis.HTMLDivElement | null>(null)
const editorTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
const isUploadingImages = computed(() => uploadingImageCount.value > 0)
const { isMobileViewport } = useViewport()
type 编辑器视图模式 = 'editor' | 'html'
type 预览类型 = 'preview' | 'html' | 'mindmap'
type 预览布局模式 = 'hidden' | 'split' | 'full'

const previewType = ref<预览类型>('preview')
const previewLayoutMode = ref<预览布局模式>('hidden')
const isMarkdownPreviewVisible = computed(() => previewType.value === 'preview' && previewLayoutMode.value !== 'hidden')
const isMarkdownSplitVisible = computed(() => previewType.value === 'preview' && previewLayoutMode.value === 'split')
const isMarkdownFullVisible = computed(() => previewType.value === 'preview' && previewLayoutMode.value === 'full')
const isMindmapPreviewVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value !== 'hidden')
const isMindmapSplitVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value === 'split')
const isMindmapFullVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value === 'full')
const isHtmlFullVisible = computed(() => previewType.value === 'html' && previewLayoutMode.value === 'full')
const 当前生效编辑器视图模式 = computed(() => 获取当前生效编辑器视图模式())
const isEditorHtmlPreviewVisible = computed(() => 当前生效编辑器视图模式.value === 'html')
const 编辑器内容区顶部偏移 = ref(0)
const 编辑器内容区底部偏移 = ref(24)
const 编辑器内容区覆盖样式 = computed(() => ({
  '--editor-content-top-offset': `${编辑器内容区顶部偏移.value}px`,
  '--editor-content-bottom-offset': `${编辑器内容区底部偏移.value}px`,
}))
const previewTypeOptions = [
  { label: '预览', value: 'preview', icon: View },
  { label: 'HTML', value: 'html', title: 'html代码预览', icon: Document },
  { label: '脑图', value: 'mindmap', icon: Connection },
] as const
const previewLayoutModeOptions = [
  { label: '关闭', value: 'hidden' },
  { label: '半边', value: 'split' },
  { label: '全部', value: 'full' },
] as const

let 编辑器尺寸观察器: globalThis.ResizeObserver | null = null
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
const 文章图片桌面摘要 = computed(() => (
  `共 ${文章图片列表项.value.length} 张，已使用 ${已使用文章图片数量.value} 张，未使用 ${未使用文章图片列表.value.length} 张`
))
const 文章图片移动端摘要 = computed(() => (
  未使用文章图片列表.value.length > 0
    ? `共 ${文章图片列表项.value.length} 张，未使用 ${未使用文章图片列表.value.length} 张`
    : `共 ${文章图片列表项.value.length} 张`
))

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

useSaveShortcut({
  enabled: () => !loading.value && !saving.value && !formatting.value && !isUploadingImages.value,
  onSave: () => {
    if (!isDirty.value) {
      ElMessage.info('没有可保存的更改')
      return
    }

    return saveArticle({ redirectAfterSave: false, syncRouteAfterSave: true })
  },
})

useEditorShortcuts({
  editorRef,
  editorId,
  enabled: () => !loading.value && !saving.value && !formatting.value && !isUploadingImages.value,
  onFormatAndSave: formatAndSaveArticle,
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
  const [categoryRecords, tagRecords] = await Promise.all([
    fetchCategories(),
    fetchTags(),
  ])
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
    const category = await createCategory(value.trim())
    categories.value.push({ label: category.name, value: category.id })
    form.value.category_id = category.id
    ElMessage.success('分类创建成功')
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(getApiErrorMessage(error, '创建分类失败'))
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
    const tag = await createTag(value.trim())
    tags.value.push({ label: tag.name, value: tag.id })
    if (!form.value.tag_ids.includes(tag.id)) {
      form.value.tag_ids.push(tag.id)
    }
    ElMessage.success('标签创建成功')
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(getApiErrorMessage(error, '创建标签失败'))
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
    const images = await fetchArticleImages(articleId)
    if (当前加载序号 !== 文章图片加载序号) {
      return
    }
    articleImages.value = images
  } catch (error) {
    if (当前加载序号 !== 文章图片加载序号) {
      return
    }

    清空文章图片状态()
    ElMessage.error(getApiErrorMessage(error, '加载文章图片失败'))
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
    const article = await fetchMyArticleById(articleId)
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
    ElMessage.error(getApiErrorMessage(error, '加载文章失败'))
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
    ElMessage.error(getApiErrorMessage(error, '加载分类和标签失败'))
  })
  void syncEditorStateFromRoute(true)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  编辑器尺寸观察器?.disconnect()
})

watch(
  [当前生效编辑器视图模式, () => editorRef.value],
  async () => {
    await nextTick()
    applyEditorViewMode(当前生效编辑器视图模式.value)
    初始化编辑器内容区尺寸观察()
  },
  { flush: 'post' },
)

watch(
  [() => editorCoreLoading.value, isMobileViewport],
  async () => {
    await nextTick()
    初始化编辑器内容区尺寸观察()
  },
  { flush: 'post' },
)

watch([previewType, previewLayoutMode], async () => {
  await nextTick()
  await new Promise<void>((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
  applyEditorViewMode(当前生效编辑器视图模式.value)
  初始化编辑器内容区尺寸观察()
})

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

function buildDraftPayload(): ArticleDraftPayload {
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
  const created = await createArticle(form.value)
  currentArticleId.value = created.id
  return created.id
}

async function updateCurrentArticle() {
  if (!currentArticleId.value) {
    throw new Error('missing_article_id')
  }

  const payload = buildUpdatePayload(form.value, savedForm.value)
  await updateArticle(currentArticleId.value, payload)
  return currentArticleId.value
}

async function syncEditorRoute(articleId: string) {
  if (!articleId) {
    return
  }
  if (route.name !== 'ArticleEditor' || getRouteArticleId() === articleId) {
    return
  }

  await router.replace({
    name: 'ArticleEditor',
    params: { id: articleId },
  })
}

async function ensureDraftArticleForImageUpload(): Promise<string> {
  if (currentArticleId.value) {
    return currentArticleId.value
  }

  const draft = await createArticleDraft(buildDraftPayload())
  currentArticleId.value = draft.id
  await syncEditorRoute(draft.id)
  return draft.id
}

function 获取当前生效编辑器视图模式(): 编辑器视图模式 {
  if (previewType.value === 'html' && previewLayoutMode.value !== 'hidden') {
    return 'html'
  }

  return 'editor'
}

function 同步编辑器内容区尺寸() {
  const 编辑器容器 = editorWrapperRef.value
  if (!编辑器容器) {
    return
  }

  const 内容区元素 = 编辑器容器.querySelector('.md-editor-content')
  if (内容区元素 instanceof globalThis.HTMLElement) {
    const 容器矩形 = 编辑器容器.getBoundingClientRect()
    const 内容区矩形 = 内容区元素.getBoundingClientRect()

    编辑器内容区顶部偏移.value = Math.max(0, 内容区矩形.top - 容器矩形.top)
    编辑器内容区底部偏移.value = Math.max(0, 容器矩形.bottom - 内容区矩形.bottom)
    return
  }

  const 工具栏元素 = 编辑器容器.querySelector('.md-editor-toolbar-wrapper')
  const 底栏元素 = 编辑器容器.querySelector('.md-editor-footer')

  编辑器内容区顶部偏移.value = 工具栏元素 instanceof globalThis.HTMLElement ? 工具栏元素.offsetHeight : 0
  编辑器内容区底部偏移.value = 底栏元素 instanceof globalThis.HTMLElement ? 底栏元素.offsetHeight : 24
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

  const 工具栏元素 = 编辑器容器.querySelector('.md-editor-toolbar-wrapper')
  const 底栏元素 = 编辑器容器.querySelector('.md-editor-footer')
  const 内容区元素 = 编辑器容器.querySelector('.md-editor-content')

  if (工具栏元素 instanceof globalThis.HTMLElement) {
    编辑器尺寸观察器.observe(工具栏元素)
  }
  if (底栏元素 instanceof globalThis.HTMLElement) {
    编辑器尺寸观察器.observe(底栏元素)
  }
  if (内容区元素 instanceof globalThis.HTMLElement) {
    编辑器尺寸观察器.observe(内容区元素)
  }
}

function applyEditorViewMode(mode: 编辑器视图模式) {
  const editor = editorRef.value

  if (!editor) {
    return
  }

  if (mode === 'editor') {
    editor.togglePreviewOnly(false)
    editor.toggleHtmlPreview(false)
    editor.togglePreview(false)
    return
  }

  editor.togglePreviewOnly(false)
  editor.togglePreview(false)
  editor.toggleHtmlPreview(true)
}

function handleBeforeUnload(event: globalThis.BeforeUnloadEvent) {
  if (!isDirty.value && !isUploadingImages.value) {
    return
  }

  event.preventDefault()
  event.returnValue = ''
}

const handleEditorImageUpload: UploadImgEvent = (files, callBack) => {
  if (files.length === 0) {
    return
  }

  uploadingImageCount.value += 1

  void (async () => {
    try {
      const articleId = await ensureDraftArticleForImageUpload()
      const uploadedFiles = await Promise.all(files.map((file) => uploadArticleImage(articleId, file)))
      await 同步文章图片(articleId)
      callBack(uploadedFiles.map((file) => file.url))
    } catch (error) {
      ElMessage.error(getApiErrorMessage(error, '图片上传失败'))
    } finally {
      uploadingImageCount.value = Math.max(0, uploadingImageCount.value - 1)
    }
  })()
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

  const editorView = editorRef.value?.getEditorView()
  const currentContent = editorView?.state.doc.toString() ?? form.value.content

  formatting.value = true
  try {
    const formattedContent = await prettierContext.prettier.format(currentContent, {
      parser: 'markdown',
      plugins: [prettierContext.markdownPlugin],
    })

    if (formattedContent === currentContent) {
      return true
    }

    if (editorView) {
      editorView.dispatch({
        changes: {
          from: 0,
          to: editorView.state.doc.length,
          insert: formattedContent,
        },
      })
    }

    form.value.content = formattedContent
    await nextTick()
    return true
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '美化失败'))
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
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
    return false
  } finally {
    saving.value = false
  }

  if (options.redirectAfterSave) {
    await router.push('/dashboard/articles')
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
  return resolveManagedFileUrl(image.thumbnail_url || image.preview_url || image.url)
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
      selectedUnusedArticleImageIds.value.map((imageId) => deleteManagedFile(imageId)),
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
      ElMessage.error(getApiErrorMessage(error, '删除文章图片失败'))
    }
  } finally {
    deletingArticleImages.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <h2 style="display: flex; align-items: center; gap: 8px; margin-bottom: 24px">
      <ElIcon><component :is="isEdit ? EditPen : DocumentAdd" /></ElIcon>
      <span>{{ isEdit ? '编辑文章' : '写文章' }}</span>
    </h2>
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
                'editor-wrapper--mindmap-split': isMindmapSplitVisible,
                'editor-wrapper--mindmap-full': isMindmapFullVisible,
                'editor-wrapper--html-full': isHtmlFullVisible,
              }"
              :style="编辑器内容区覆盖样式"
            >
              <div v-if="editorCoreLoading" class="editor-loading">
                正在加载编辑器...
              </div>
              <MdEditor
                :id="editorId"
                ref="editorRef"
                v-model="form.content"
                class="article-md-editor"
                :on-upload-img="handleEditorImageUpload"
                :preview="false"
                :html-preview="isEditorHtmlPreviewVisible"
                :theme="editorTheme"
                preview-theme="github"
                code-theme="github"
                language="zh-CN"
                placeholder="在此编写 Markdown 内容..."
                :toolbars-exclude="['github', 'save', 'catalog', 'preview', 'previewOnly', 'htmlPreview']"
              />

              <div v-if="isMarkdownPreviewVisible" class="markdown-editor-overlay">
                <MarkdownRenderer
                  class="markdown-editor-overlay__content article-markdown-preview"
                  :content="form.content"
                />
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

        <section class="article-image-panel">
          <div class="article-image-panel__header">
            <div
              class="article-image-panel__header-main"
              :class="{ 'is-expanded': articleImagePanelExpanded }"
            >
              <div class="article-image-panel__header-info">
                <div class="article-image-panel__title">文章图片</div>
                <div class="article-image-panel__header-summary article-image-panel__header-summary--desktop">
                  {{ 文章图片桌面摘要 }}
                </div>
                <div class="article-image-panel__header-summary article-image-panel__header-summary--mobile">
                  {{ 文章图片移动端摘要 }}
                </div>
              </div>
              <div v-if="articleImagePanelExpanded" class="article-image-panel__actions">
                <ElButton size="small" :disabled="!currentArticleId || articleImagesLoading" @click="同步文章图片(currentArticleId)">
                  刷新
                </ElButton>
                <ElButton
                  size="small"
                  :disabled="未使用文章图片列表.length === 0 || deletingArticleImages"
                  @click="选中全部未使用文章图片"
                >
                  选中未使用
                </ElButton>
                <ElButton
                  size="small"
                  :disabled="selectedUnusedArticleImageIds.length === 0"
                  @click="清空未使用文章图片选择"
                >
                  清空选择
                </ElButton>
                <ElButton
                  size="small"
                  type="danger"
                  :loading="deletingArticleImages"
                  :disabled="selectedUnusedArticleImageIds.length === 0"
                  @click="删除选中未使用文章图片"
                >
                  删除选中未使用图片
                </ElButton>
              </div>
              <ElButton class="article-image-panel__toggle" size="small" @click="切换文章图片面板展开状态">
                {{ articleImagePanelExpanded ? '收起' : '展开' }}
              </ElButton>
            </div>
          </div>

          <div v-if="articleImagePanelExpanded && !currentArticleId" class="article-image-panel__placeholder">
            首次上传正文图片时会自动创建草稿，随后这里会显示该文章的全部图片，并标记哪些图片当前未被正文或封面引用。
          </div>

          <div v-else-if="articleImagePanelExpanded && articleImagesLoading && articleImages.length === 0" class="article-image-panel__placeholder">
            正在加载文章图片...
          </div>

          <ElEmpty v-else-if="articleImagePanelExpanded && 文章图片列表项.length === 0" description="当前文章还没有上传图片" />

          <div v-else-if="articleImagePanelExpanded" class="article-image-grid">
            <article
              v-for="image in 文章图片列表项"
              :key="image.id"
              class="article-image-card"
              :class="{
                'is-used': image.isUsed,
                'is-selected': selectedUnusedArticleImageIds.includes(image.id),
              }"
            >
              <div class="article-image-card__toolbar">
                <ElCheckbox
                  v-if="!image.isUsed"
                  :model-value="selectedUnusedArticleImageIds.includes(image.id)"
                  @change="切换未使用文章图片选择(image.id, Boolean($event))"
                >
                  选择删除
                </ElCheckbox>
                <span v-else class="article-image-card__locked-tip">当前已被正文或封面引用</span>
                <ElTag :type="image.isUsed ? 'success' : 'warning'" size="small">
                  {{ image.isUsed ? '已使用' : '未使用' }}
                </ElTag>
              </div>

              <div class="article-image-card__preview">
                <img :src="获取文章图片预览地址(image)" :alt="image.original_name">
              </div>

              <div class="article-image-card__body">
                <div class="article-image-card__name" :title="image.original_name">{{ image.original_name }}</div>
                <div class="article-image-card__meta">
                  <span>{{ 格式化文章图片大小(image.size) }}</span>
                  <span>{{ 格式化文章图片时间(image.created_at) }}</span>
                </div>
                <div class="article-image-card__hint">
                  {{ image.isUsed ? '保留中：当前正文或封面仍在引用这张图片' : '可清理：当前正文和封面都没引用这张图片' }}
                </div>
              </div>
            </article>
          </div>
        </section>

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
  position: relative;
  width: 100%;
  min-width: 0;
  border-radius: 12px;
  overflow: hidden;
  background: transparent;
}

.editor-loading {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(3px);
}

.editor-wrapper--markdown-split :deep(.md-editor-input-wrapper),
.editor-wrapper--mindmap-split :deep(.md-editor-input-wrapper) {
  flex: 0 0 50%;
  width: 50% !important;
  max-width: 50%;
}

.editor-wrapper--markdown-split :deep(.md-editor-content),
.editor-wrapper--mindmap-split :deep(.md-editor-content) {
  background:
    linear-gradient(
      90deg,
      transparent 0,
      transparent calc(50% - 0.5px),
      var(--el-border-color) calc(50% - 0.5px),
      var(--el-border-color) calc(50% + 0.5px),
      transparent calc(50% + 0.5px),
      transparent 100%
    );
}

.editor-wrapper--markdown-full :deep(.md-editor-content),
.editor-wrapper--mindmap-full :deep(.md-editor-content) {
  visibility: hidden;
  pointer-events: none;
}

.editor-wrapper--html-full :deep(.md-editor-input-wrapper) {
  width: 0 !important;
  max-width: 0;
  flex: 0 0 0 !important;
  overflow: hidden;
}

.editor-wrapper--html-full :deep(.md-editor-resize-operate) {
  display: none !important;
}

.editor-wrapper--html-full :deep(.md-editor-preview-wrapper) {
  width: 100%;
  max-width: 100%;
  flex: 1 1 100%;
}

.markdown-editor-overlay,
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
  background: var(--el-bg-color-overlay);
}

.editor-wrapper--markdown-split .markdown-editor-overlay,
.editor-wrapper--mindmap-split .mindmap-editor-overlay {
  left: 50%;
  border-left: 1px solid color-mix(in srgb, var(--el-border-color) 88%, var(--el-text-color-secondary));
  box-shadow: inset 1px 0 0 color-mix(in srgb, var(--el-bg-color-overlay) 70%, transparent);
}

.markdown-editor-overlay__content {
  min-height: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
}

.mindmap-editor-overlay :deep(.markdown-mindmap) {
  min-height: 100%;
  height: 100%;
  border: none;
  border-radius: 0;
}

.article-md-editor {
  width: 100%;
  height: 720px;
}

.article-md-editor:deep(.md-editor) {
  width: 100%;
  border: none;
  background: transparent;
  border-radius: 12px;
}

.article-md-editor:deep(.md-editor-previewOnly) {
  height: 100%;
  overflow: hidden;
}

.article-md-editor:deep(.md-editor-toolbar),
.article-md-editor:deep(.md-editor-footer) {
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
}

.article-md-editor:deep(.md-editor-toolbar) {
  border: none;
}

.article-md-editor:deep(.md-editor-toolbar-wrapper) {
  background: var(--el-bg-color-overlay);
}

.article-md-editor:deep(.md-editor-toolbar svg),
.article-md-editor:deep(.md-editor-footer svg) {
  color: var(--el-text-color-primary);
}

.article-md-editor:deep(.md-editor-toolbar-item),
.article-md-editor:deep(.md-editor-toolbar-item button),
.article-md-editor:deep(.md-editor-toolbar-item span),
.article-md-editor:deep(.md-editor-toolbar-item i) {
  color: var(--el-text-color-primary);
}

.article-md-editor:deep(.md-editor-content) {
  display: flex;
  width: 100%;
  min-width: 0;
  border-inline: none;
}

.article-md-editor:deep(.md-editor-footer) {
  display: flex;
  align-items: center;
  min-height: 24px;
  border: none;
  border-bottom-right-radius: 12px;
  border-bottom-left-radius: 12px;
}

.article-md-editor:deep(.md-editor-footer-left),
.article-md-editor:deep(.md-editor-footer-right) {
  display: flex;
  align-items: center;
}

.article-md-editor:deep(.md-editor-input-wrapper),
.article-md-editor:deep(.md-editor-preview-wrapper) {
  flex: 1 1 0;
  min-width: 0;
}

.article-md-editor:deep(.md-editor-footer-item) {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding-block: 0;
}

.article-md-editor:deep(.md-editor-footer-label) {
  display: inline-flex;
  align-items: center;
}

.article-md-editor:deep(.md-editor-footer-left),
.article-md-editor:deep(.md-editor-footer-right),
.article-md-editor:deep(.md-editor-footer-item span),
.article-md-editor:deep(.md-editor-footer-label) {
  color: var(--el-text-color-secondary);
  line-height: 1;
}

.article-md-editor:deep(.md-editor-input-wrapper),
.article-md-editor:deep(.md-editor-preview-wrapper) {
  font-size: 14px;
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

.article-image-panel {
  display: grid;
  gap: 16px;
  margin-bottom: 24px;
  padding: 18px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--el-color-success-light-9) 34%, transparent), transparent 42%),
    var(--el-bg-color-overlay);
}

.article-image-panel__header {
  display: grid;
  gap: 12px;
}

.article-image-panel__header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: nowrap;
  min-width: 0;
}

.article-image-panel__header-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1 1 auto;
  min-width: 0;
}

.article-image-panel__title {
  flex: 0 0 auto;
  font-size: 16px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.article-image-panel__header-summary {
  flex: 1 1 auto;
  min-width: 0;
}

.article-image-panel__header-summary--mobile {
  display: none;
}

.article-image-panel__header-summary,
.article-image-panel__placeholder {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.article-image-panel__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
  flex: 0 0 auto;
}

.article-image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.article-image-card {
  display: grid;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 14px;
  background: var(--el-bg-color);
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.article-image-card.is-used {
  border-color: color-mix(in srgb, var(--el-color-success) 34%, var(--el-border-color-light));
}

.article-image-card.is-selected {
  border-color: var(--el-color-danger);
  box-shadow: 0 10px 24px rgba(245, 108, 108, 0.16);
}

.article-image-card:hover {
  transform: translateY(-2px);
}

.article-image-card__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.article-image-card__locked-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.article-image-card__preview {
  overflow: hidden;
  aspect-ratio: 16 / 10;
  border-radius: 10px;
  background:
    linear-gradient(135deg, var(--theme-accent-overlay-10), color-mix(in srgb, var(--el-color-primary-light-3) 12%, transparent)),
    var(--el-fill-color-light);
}

.article-image-card__preview img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.article-image-card__body {
  display: grid;
  gap: 8px;
}

.article-image-card__name {
  color: var(--el-text-color-primary);
  font-weight: 600;
  line-height: 1.5;
  word-break: break-all;
}

.article-image-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.article-image-card__hint {
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 1.6;
}

:global(.dark .article-md-editor .md-editor-toolbar),
:global(.dark .article-md-editor .md-editor-toolbar-wrapper) {
  --md-color: #fff !important;
  --md-hover-color: #fff !important;
}

:global(.dark .article-md-editor .md-editor-toolbar-item),
:global(.dark .article-md-editor .md-editor-toolbar-item button),
:global(.dark .article-md-editor .md-editor-toolbar-item span),
:global(.dark .article-md-editor .md-editor-toolbar-item i),
:global(.dark .article-md-editor .md-editor-toolbar-item svg) {
  color: #fff !important;
}

:global(.dark .article-md-editor .md-editor-toolbar-item svg),
:global(.dark .article-md-editor .md-editor-toolbar-item svg *) {
  stroke: #fff !important;
}

:global(.dark .editor-loading) {
  background: rgba(15, 23, 42, 0.72);
  color: var(--text-secondary);
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

  .article-image-panel {
    padding: 14px;
  }

  .markdown-editor-overlay__content {
    padding: 16px;
  }

  .article-image-panel__actions {
    width: 100%;
    flex-wrap: wrap;
    order: 3;
  }

  .article-image-panel__header-main {
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .article-image-panel__header-info {
    align-items: center;
    justify-content: space-between;
    flex: 1 1 auto;
    min-width: 0;
    gap: 12px;
  }

  .article-image-panel__header-main.is-expanded .article-image-panel__header-info {
    flex: 1 1 calc(100% - 96px);
  }

  .article-image-panel__header-summary--desktop {
    display: none;
  }

  .article-image-panel__header-summary--mobile {
    display: block;
    order: 2;
    width: 100%;
    text-align: center;
  }

  .article-image-panel__actions :deep(.el-button) {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
    margin-left: 0;
  }

  .article-image-grid {
    grid-template-columns: 1fr;
  }

  .article-md-editor {
    height: 560px;
  }

  .article-editor-actions {
    align-items: stretch;
  }

  .article-editor-buttons {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
