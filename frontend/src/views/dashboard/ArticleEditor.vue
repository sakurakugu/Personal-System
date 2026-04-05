<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import {
  ElButton, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElMessageBox, ElOption, ElSelect, ElSkeleton,
} from 'element-plus'
import { Connection, Document, DocumentAdd, EditPen, View } from '@element-plus/icons-vue'
import type { ExposeParam } from 'md-editor-v3'
import SegmentedSwitch from '../../components/SegmentedSwitch.vue'
import { useEditorShortcuts } from '../../composables/useEditorShortcuts'
import { useSaveShortcut } from '../../composables/useSaveShortcut'
import { useViewport } from '../../composables/useViewport'
import {
  createArticle,
  fetchCategories,
  fetchMyArticleById,
  fetchTags,
  updateArticle,
} from '../../features/articles/api'
import type { ArticleEditorPayload } from '../../features/articles/types'
import { useThemeStore } from '../../stores/theme'
import { getApiErrorMessage } from '../../utils/api'

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

const isEdit = ref(false)
const loading = ref(false)
const saving = ref(false)
const formatting = ref(false)
const editorId = 'article-editor'
const editorRef = ref<ExposeParam>()
const editorWrapperRef = ref<globalThis.HTMLDivElement | null>(null)
const editorTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
const { isMobileViewport } = useViewport()
type 编辑器视图模式 = 'editor' | 'preview' | 'preview-only' | 'html'
type 预览类型 = 'preview' | 'html' | 'mindmap'
type 预览布局模式 = 'hidden' | 'split' | 'full'

const previewType = ref<预览类型>('preview')
const previewLayoutMode = ref<预览布局模式>('hidden')
const isMindmapPreviewVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value !== 'hidden')
const isMindmapSplitVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value === 'split')
const isMindmapFullVisible = computed(() => previewType.value === 'mindmap' && previewLayoutMode.value === 'full')
const isHtmlFullVisible = computed(() => previewType.value === 'html' && previewLayoutMode.value === 'full')
const 当前生效编辑器视图模式 = computed(() => 获取当前生效编辑器视图模式())
const isEditorPreviewVisible = computed(() => (
  当前生效编辑器视图模式.value === 'preview' || 当前生效编辑器视图模式.value === 'preview-only'
))
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

interface SelectOption {
  label: string
  value: string
}

const form = ref<ArticleEditorPayload>({
  title: '',
  content: '',
  excerpt: '',
  cover_url: '',
  status: 'private',
  category_id: null as string | null,
  tag_ids: [] as string[],
})
const savedSnapshot = ref(JSON.stringify({
  ...form.value,
  category_id: form.value.category_id ?? null,
  tag_ids: [...form.value.tag_ids].sort(),
}))

const articleStatusOptions = [
  { label: '私有', value: 'private' },
  { label: '登录可见', value: 'login_required' },
  { label: '公开', value: 'public' },
] as const

const categories = ref<SelectOption[]>([])
const tags = ref<SelectOption[]>([])
const isDirty = computed(() => buildFormSnapshot(form.value) !== savedSnapshot.value)

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

useSaveShortcut({
  enabled: () => !loading.value && !saving.value && !formatting.value,
  onSave: () => {
    if (!isDirty.value) {
      ElMessage.info('没有可保存的更改')
      return
    }

    return saveArticle({ redirectAfterSave: false })
  },
})

useEditorShortcuts({
  editorRef,
  editorId,
  enabled: () => !loading.value && !saving.value && !formatting.value,
  onFormatAndSave: formatAndSaveArticle,
})

onMounted(async () => {
  previewType.value = 'preview'
  previewLayoutMode.value = isMobileViewport.value ? 'hidden' : 'split'

  const [categoryRecords, tagRecords] = await Promise.all([
    fetchCategories(),
    fetchTags(),
  ])
  categories.value = categoryRecords.map((category) => ({ label: category.name, value: category.id }))
  tags.value = tagRecords.map((tag) => ({ label: tag.name, value: tag.id }))

  const id = route.params.id as string
  if (id) {
    isEdit.value = true
    loading.value = true
    try {
      const full = await fetchMyArticleById(id)
      form.value = {
        title: full.title,
        content: full.content,
        excerpt: full.excerpt || '',
        cover_url: full.cover_url || '',
        status: full.status,
        category_id: full.category?.id || null,
        tag_ids: full.tags.map((tag) => tag.id),
      }
    } finally {
      loading.value = false
    }
  }

  markFormSaved()
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

onBeforeRouteLeave(async () => {
  if (saving.value || formatting.value) {
    ElMessage.warning(formatting.value ? '正在美化内容，请稍后' : '正在保存，请稍后')
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
    return await saveArticle({ redirectAfterSave: false })
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
  savedSnapshot.value = buildFormSnapshot(form.value)
}

function 获取当前生效编辑器视图模式(): 编辑器视图模式 {
  if (previewType.value === 'preview') {
    if (previewLayoutMode.value === 'hidden') {
      return 'editor'
    }
    if (previewLayoutMode.value === 'split') {
      return 'preview'
    }

    return 'preview-only'
  }

  if (previewType.value === 'html') {
    if (previewLayoutMode.value === 'hidden') {
      return 'editor'
    }

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

  if (mode === 'preview') {
    editor.togglePreviewOnly(false)
    editor.toggleHtmlPreview(false)
    editor.togglePreview(true)
    return
  }

  if (mode === 'preview-only') {
    editor.toggleHtmlPreview(false)
    editor.togglePreview(true)
    editor.togglePreviewOnly(true)
    return
  }

  editor.togglePreviewOnly(false)
  editor.togglePreview(false)
  editor.toggleHtmlPreview(true)
}

function handleBeforeUnload(event: globalThis.BeforeUnloadEvent) {
  if (!isDirty.value) {
    return
  }

  event.preventDefault()
  event.returnValue = ''
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

  return saveArticle({ redirectAfterSave: false })
}

async function saveArticle(options: { redirectAfterSave: boolean }): Promise<boolean> {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return false
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateArticle(String(route.params.id), form.value)
      ElMessage.success('更新成功')
    } else {
      const created = await createArticle(form.value)
      isEdit.value = true
      ElMessage.success('创建成功')
      if (!options.redirectAfterSave) {
        await router.replace({
          name: 'ArticleEditor',
          params: { id: created.id },
        })
      }
    }
    markFormSaved()
    if (options.redirectAfterSave) {
      await router.push('/dashboard/articles')
    }
    return true
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存失败'))
    return false
  } finally {
    saving.value = false
  }
}

async function save() {
  await saveArticle({ redirectAfterSave: true })
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
          <ElFormItem label="分类">
            <ElSelect v-model="form.category_id" placeholder="选择分类" clearable>
              <ElOption v-for="item in categories" :key="item.value" :label="item.label" :value="item.value" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="标签">
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
                  active-color="#18a058"
                  size="small"
                />
                <SegmentedSwitch
                  v-model="previewLayoutMode"
                  aria-label="文章预览显示方式"
                  :options="previewLayoutModeOptions"
                  active-color="#18a058"
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
                :preview="isEditorPreviewVisible"
                :html-preview="isEditorHtmlPreviewVisible"
                :theme="editorTheme"
                preview-theme="github"
                code-theme="github"
                language="zh-CN"
                placeholder="在此编写 Markdown 内容..."
                :toolbars-exclude="['github', 'save', 'catalog', 'preview', 'previewOnly', 'htmlPreview']"
              />

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

        <div class="article-editor-actions">
          <ElFormItem label="状态" class="article-editor-status">
            <SegmentedSwitch
              v-model="form.status"
              aria-label="文章状态"
              :options="articleStatusOptions"
              active-color="#18a058"
            />
          </ElFormItem>

          <div class="article-editor-buttons">
            <ElButton type="primary" :loading="saving || formatting" @click="save">
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

.editor-wrapper--mindmap-split :deep(.md-editor-input-wrapper) {
  flex: 0 0 50%;
  width: 50% !important;
  max-width: 50%;
}

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

.mindmap-editor-overlay {
  position: absolute;
  inset:
    var(--editor-content-top-offset, 0px)
    0
    var(--editor-content-bottom-offset, 24px)
    0;
  z-index: 2;
}

.editor-wrapper--mindmap-split .mindmap-editor-overlay {
  left: 50%;
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

  .editor-form-item__controls :deep(.segmented-switch) {
    width: 100%;
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
