<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import {
  ElButton, ElForm, ElFormItem, ElIcon, ElInput, ElMessage, ElMessageBox, ElOption, ElSelect, ElSkeleton,
} from 'element-plus'
import { EditPen, DocumentAdd } from '@element-plus/icons-vue'
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
const editorTheme = computed(() => (themeStore.isDark ? 'dark' : 'light'))
const { isMobileViewport } = useViewport()
const editorViewMode = ref<'editor' | 'markdown' | 'mindmap'>('markdown')
const isEditorPreviewVisible = computed(() => editorViewMode.value === 'markdown')
const mindmapPreviewHeight = computed(() => (isMobileViewport.value ? 520 : 720))

const editorViewModeOptions = [
  { label: '仅编辑', value: 'editor' },
  { label: 'Markdown 预览', value: 'markdown' },
  { label: '思维导图', value: 'mindmap' },
] as const

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
  editorViewMode.value = isMobileViewport.value ? 'editor' : 'markdown'

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

        <ElFormItem label="正文 (Markdown)">
          <div class="editor-mode-switch">
            <SegmentedSwitch
              v-model="editorViewMode"
              aria-label="文章编辑视图模式"
              :options="editorViewModeOptions"
              active-color="#18a058"
              size="small"
            />
          </div>

          <div class="editor-workspace" :class="{ 'editor-workspace--mindmap': editorViewMode === 'mindmap' }">
            <div class="editor-wrapper">
              <div v-if="editorCoreLoading" class="editor-loading">
                正在加载编辑器...
              </div>
              <MdEditor
                :id="editorId"
                ref="editorRef"
                v-model="form.content"
                class="article-md-editor"
                :preview="isEditorPreviewVisible"
                :theme="editorTheme"
                preview-theme="github"
                code-theme="github"
                language="zh-CN"
                placeholder="在此编写 Markdown 内容..."
                :toolbars-exclude="['github', 'save', 'catalog']"
              />
            </div>

            <div v-if="editorViewMode === 'mindmap'" class="mindmap-preview-panel">
              <div class="mindmap-preview-panel__title">思维导图预览</div>
              <MarkdownMindmap
                :content="form.content"
                :title="form.title"
                :height="mindmapPreviewHeight"
              />
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

.editor-mode-switch {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.editor-workspace {
  display: block;
}

.editor-workspace--mindmap {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 16px;
  align-items: stretch;
}

.editor-wrapper {
  position: relative;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  background: transparent;
}

.editor-loading {
  position: absolute;
  inset: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(3px);
}

.mindmap-preview-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.mindmap-preview-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
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

  .editor-mode-switch :deep(.segmented-switch) {
    width: 100%;
  }

  .editor-workspace--mindmap {
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
