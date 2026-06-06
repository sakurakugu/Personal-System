<script setup lang="ts">
import { commandsCtx, Editor, defaultValueCtx, editorViewCtx, rootCtx, serializerCtx } from '@milkdown/core'
import { history } from '@milkdown/plugin-history'
import { listener, listenerCtx } from '@milkdown/plugin-listener'
import { clipboard } from '@milkdown/plugin-clipboard'
import { cursor } from '@milkdown/plugin-cursor'
import { indent } from '@milkdown/plugin-indent'
import { trailing } from '@milkdown/plugin-trailing'
import {
  commonmark,
  createCodeBlockCommand,
  insertHrCommand,
  toggleEmphasisCommand,
  toggleInlineCodeCommand,
  toggleLinkCommand,
  toggleStrongCommand,
  wrapInBlockquoteCommand,
  wrapInBulletListCommand,
  wrapInHeadingCommand,
  wrapInOrderedListCommand,
} from '@milkdown/preset-commonmark'
import { gfm } from '@milkdown/preset-gfm'
import { insertTableCommand } from '@milkdown/preset-gfm'
import { redo } from '@milkdown/prose/history'
import { insert, replaceAll } from '@milkdown/utils'
import type { EditorView } from '@milkdown/prose/view'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export interface MilkdownMarkdownImagePayload {
  url: string
  alt?: string
  title?: string
}

export type MilkdownMarkdownImageUploader = (
  files: File[],
) => Promise<MilkdownMarkdownImagePayload[]>

export interface MilkdownMarkdown编辑器实例 {
  getMarkdown: () => string
  setMarkdown: (markdown: string) => void
  insertMarkdown: (markdown: string) => void
  getEditorView: () => EditorView | null
  redo: () => boolean
  focus: () => void
}

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  theme?: 'light' | 'dark'
  uploadImages?: MilkdownMarkdownImageUploader
}>(), {
  placeholder: '在此编写 Markdown 内容...',
  theme: 'light',
  uploadImages: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  ready: []
  loadingChange: [value: boolean]
  uploadError: [error: unknown]
}>()

const rootRef = ref<HTMLDivElement | null>(null)
const sourceTextareaRef = ref<HTMLTextAreaElement | null>(null)
const editor = ref<Editor | null>(null)
const loading = ref(true)
const isSourceMode = ref(false)
const sourceContent = ref('')
const lastMarkdown = ref(props.modelValue)
const isApplyingExternalMarkdown = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

type ToolbarAction =
  | 'source'
  | 'heading'
  | 'strong'
  | 'emphasis'
  | 'link'
  | 'inlineCode'
  | 'blockquote'
  | 'bulletList'
  | 'orderedList'
  | 'codeBlock'
  | 'table'
  | 'hr'
  | 'image'

const toolbarGroups: Array<Array<{ label: string; title: string; action: ToolbarAction }>> = [
  [
    { label: 'H2', title: '二级标题', action: 'heading' },
    { label: 'B', title: '加粗', action: 'strong' },
    { label: 'I', title: '斜体', action: 'emphasis' },
    { label: '`', title: '行内代码', action: 'inlineCode' },
    { label: '链接', title: '插入链接', action: 'link' },
  ],
  [
    { label: '引用', title: '引用块', action: 'blockquote' },
    { label: '列表', title: '无序列表', action: 'bulletList' },
    { label: '编号', title: '有序列表', action: 'orderedList' },
    { label: '代码块', title: '代码块', action: 'codeBlock' },
    { label: '表格', title: '插入表格', action: 'table' },
    { label: '分割线', title: '分割线', action: 'hr' },
  ],
]

const rootClass = computed(() => ({
  'milkdown-markdown-editor--dark': props.theme === 'dark',
  'milkdown-markdown-editor--source': isSourceMode.value,
  'milkdown-markdown-editor--uploading': isUploading.value,
}))

onMounted(async () => {
  await nextTick()
  await createEditor()
})

onBeforeUnmount(() => {
  void editor.value?.destroy()
  editor.value = null
})

watch(
  () => props.modelValue,
  (value) => {
    if (value === lastMarkdown.value) {
      return
    }

    lastMarkdown.value = value
    if (isSourceMode.value) {
      sourceContent.value = value
      return
    }

    setMarkdown(value)
  },
)

watch(isSourceMode, async (sourceMode) => {
  if (sourceMode) {
    sourceContent.value = getMarkdown()
    await nextTick()
    sourceTextareaRef.value?.focus()
    return
  }

  setMarkdown(sourceContent.value)
  await nextTick()
  getEditorView()?.focus()
})

async function createEditor() {
  const root = rootRef.value
  if (!root) {
    return
  }

  loading.value = true
  emit('loadingChange', true)

  const milkdownEditor = Editor.make()
    .config((ctx) => {
      ctx.set(rootCtx, root)
      ctx.set(defaultValueCtx, props.modelValue)
      ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
        if (isApplyingExternalMarkdown.value) {
          return
        }

        lastMarkdown.value = markdown
        emit('update:modelValue', markdown)
      })
    })
    .use(commonmark)
    .use(gfm)
    .use(history)
    .use(listener)
    .use(clipboard)
    .use(cursor)
    .use(indent)
    .use(trailing)

  try {
    editor.value = await milkdownEditor.create()
    lastMarkdown.value = props.modelValue
    emit('ready')
  } finally {
    loading.value = false
    emit('loadingChange', false)
  }
}

function getMarkdown(): string {
  const currentEditor = editor.value
  if (!currentEditor) {
    return isSourceMode.value ? sourceContent.value : lastMarkdown.value
  }

  return currentEditor.action((ctx) => {
    const view = ctx.get(editorViewCtx)
    const serializer = ctx.get(serializerCtx)
    return serializer(view.state.doc)
  })
}

function setMarkdown(markdown: string) {
  lastMarkdown.value = markdown

  if (isSourceMode.value) {
    sourceContent.value = markdown
    return
  }

  const currentEditor = editor.value
  if (!currentEditor) {
    return
  }

  isApplyingExternalMarkdown.value = true
  currentEditor.action(replaceAll(markdown, true))
  isApplyingExternalMarkdown.value = false
}

function insertMarkdown(markdown: string) {
  if (!markdown) {
    return
  }

  if (isSourceMode.value) {
    const textarea = sourceTextareaRef.value
    const selectionStart = textarea?.selectionStart ?? sourceContent.value.length
    const selectionEnd = textarea?.selectionEnd ?? selectionStart
    sourceContent.value = `${sourceContent.value.slice(0, selectionStart)}${markdown}${sourceContent.value.slice(selectionEnd)}`
    handleSourceInput()
    return
  }

  const currentEditor = editor.value
  if (!currentEditor) {
    return
  }

  currentEditor.action(insert(markdown))
  lastMarkdown.value = getMarkdown()
  emit('update:modelValue', lastMarkdown.value)
}

function getEditorView(): EditorView | null {
  return editor.value?.action((ctx) => ctx.get(editorViewCtx)) ?? null
}

function redoEdit(): boolean {
  const view = getEditorView()
  if (!view) {
    return false
  }

  return redo(view.state, view.dispatch)
}

function focus() {
  if (isSourceMode.value) {
    sourceTextareaRef.value?.focus()
    return
  }

  getEditorView()?.focus()
}

function handleSourceInput() {
  lastMarkdown.value = sourceContent.value
  emit('update:modelValue', sourceContent.value)
}

function toggleSourceMode() {
  isSourceMode.value = !isSourceMode.value
}

function runToolbarAction(action: ToolbarAction) {
  if (action === 'source') {
    toggleSourceMode()
    return
  }

  if (action === 'image') {
    openImagePicker()
    return
  }

  if (isSourceMode.value) {
    runSourceModeAction(action)
    return
  }

  const currentEditor = editor.value
  if (!currentEditor) {
    return
  }

  const commandResult = currentEditor.action((ctx) => {
    const commands = ctx.get(commandsCtx)
    switch (action) {
      case 'heading':
        return commands.call(wrapInHeadingCommand.key, 2)
      case 'strong':
        return commands.call(toggleStrongCommand.key)
      case 'emphasis':
        return commands.call(toggleEmphasisCommand.key)
      case 'inlineCode':
        return commands.call(toggleInlineCodeCommand.key)
      case 'link':
        return commands.call(toggleLinkCommand.key, { href: 'https://example.com' })
      case 'blockquote':
        return commands.call(wrapInBlockquoteCommand.key)
      case 'bulletList':
        return commands.call(wrapInBulletListCommand.key)
      case 'orderedList':
        return commands.call(wrapInOrderedListCommand.key)
      case 'codeBlock':
        return commands.call(createCodeBlockCommand.key)
      case 'table':
        return commands.call(insertTableCommand.key, { row: 3, col: 3 })
      case 'hr':
        return commands.call(insertHrCommand.key)
    }
  })

  if (!commandResult) {
    runSourceModeAction(action)
  }

  lastMarkdown.value = getMarkdown()
  emit('update:modelValue', lastMarkdown.value)
  focus()
}

function runSourceModeAction(action: ToolbarAction) {
  switch (action) {
    case 'heading':
      insertMarkdown('\n## 标题\n')
      return
    case 'strong':
      insertMarkdown('**加粗文本**')
      return
    case 'emphasis':
      insertMarkdown('*斜体文本*')
      return
    case 'inlineCode':
      insertMarkdown('`代码`')
      return
    case 'link':
      insertMarkdown('[链接文本](https://example.com)')
      return
    case 'blockquote':
      insertMarkdown('\n> 引用内容\n')
      return
    case 'bulletList':
      insertMarkdown('\n- 列表项\n')
      return
    case 'orderedList':
      insertMarkdown('\n1. 列表项\n')
      return
    case 'codeBlock':
      insertMarkdown('\n```ts\n\n```\n')
      return
    case 'table':
      insertMarkdown('\n| 列 A | 列 B | 列 C |\n| --- | --- | --- |\n|  |  |  |\n|  |  |  |\n')
      return
    case 'hr':
      insertMarkdown('\n---\n')
      return
    case 'source':
    case 'image':
      return
  }
}

function openImagePicker() {
  if (!props.uploadImages || isUploading.value) {
    return
  }

  fileInputRef.value?.click()
}

function handleFileInputChange(event: Event) {
  const input = event.target
  if (!(input instanceof HTMLInputElement)) {
    return
  }

  void uploadAndInsertImages(Array.from(input.files ?? []))
  input.value = ''
}

function handleEditorPaste(event: ClipboardEvent) {
  const files = Array.from(event.clipboardData?.files ?? []).filter((file) => file.type.startsWith('image/'))
  if (files.length === 0) {
    return
  }

  event.preventDefault()
  void uploadAndInsertImages(files)
}

function handleEditorDrop(event: DragEvent) {
  const files = Array.from(event.dataTransfer?.files ?? []).filter((file) => file.type.startsWith('image/'))
  if (files.length === 0) {
    return
  }

  event.preventDefault()
  void uploadAndInsertImages(files)
}

async function uploadAndInsertImages(files: File[]) {
  if (!props.uploadImages || files.length === 0) {
    return
  }

  isUploading.value = true
  try {
    const uploadedImages = await props.uploadImages(files)
    const markdown = uploadedImages
      .map((image) => formatMarkdownImage(image))
      .filter((value) => value.length > 0)
      .join('\n\n')

    if (markdown) {
      insertMarkdown(`\n${markdown}\n`)
    }
  } catch (error) {
    emit('uploadError', error)
  } finally {
    isUploading.value = false
  }
}

function formatMarkdownImage(image: MilkdownMarkdownImagePayload): string {
  const alt = image.alt ?? ''
  const title = image.title?.trim()
  const titlePart = title ? ` "${title.replace(/"/g, '\\"')}"` : ''
  return `![${alt}](${image.url}${titlePart})`
}

defineExpose<MilkdownMarkdown编辑器实例>({
  getMarkdown,
  setMarkdown,
  insertMarkdown,
  getEditorView,
  redo: redoEdit,
  focus,
})
</script>

<template>
  <div
    class="milkdown-markdown-editor"
    :class="rootClass"
    @paste="handleEditorPaste"
    @drop="handleEditorDrop"
  >
    <div class="milkdown-markdown-editor__toolbar">
      <div
        v-for="(group, groupIndex) in toolbarGroups"
        :key="groupIndex"
        class="milkdown-markdown-editor__toolbar-group"
      >
        <button
          v-for="item in group"
          :key="item.action"
          class="milkdown-markdown-editor__toolbar-button"
          type="button"
          :title="item.title"
          @click="runToolbarAction(item.action)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="milkdown-markdown-editor__toolbar-group milkdown-markdown-editor__toolbar-group--tail">
        <button
          v-if="uploadImages"
          class="milkdown-markdown-editor__toolbar-button"
          type="button"
          title="插入图片"
          :disabled="isUploading"
          @click="runToolbarAction('image')"
        >
          {{ isUploading ? '上传中...' : '图片' }}
        </button>
        <button
          class="milkdown-markdown-editor__toolbar-button"
          type="button"
          :aria-pressed="isSourceMode"
          :title="isSourceMode ? '切换到所见即所得' : '切换到源码编辑'"
          @click="runToolbarAction('source')"
        >
          {{ isSourceMode ? '所见即所得' : '源码' }}
        </button>
      </div>
      <input
        ref="fileInputRef"
        class="milkdown-markdown-editor__file-input"
        type="file"
        accept="image/*"
        multiple
        @change="handleFileInputChange"
      >
    </div>

    <div class="milkdown-markdown-editor__content">
      <div
        v-show="!isSourceMode"
        ref="rootRef"
        class="milkdown-markdown-editor__milkdown"
        :data-placeholder="placeholder"
      />
      <textarea
        v-show="isSourceMode"
        ref="sourceTextareaRef"
        v-model="sourceContent"
        class="milkdown-markdown-editor__source"
        :placeholder="placeholder"
        @input="handleSourceInput"
      />
      <div v-if="loading" class="milkdown-markdown-editor__loading">
        正在加载编辑器...
      </div>
    </div>
  </div>
</template>

<style scoped>
.milkdown-markdown-editor {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 720px;
  min-height: 360px;
  overflow: hidden;
  border-radius: 12px;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
}

.milkdown-markdown-editor__toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 6px 10px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color);
  background: var(--el-bg-color-overlay);
  overflow-x: auto;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__toolbar-group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
}

.milkdown-markdown-editor__toolbar-group + .milkdown-markdown-editor__toolbar-group {
  padding-left: 10px;
  border-left: 1px solid var(--el-border-color);
}

.milkdown-markdown-editor__toolbar-group--tail {
  margin-left: auto;
}

.milkdown-markdown-editor__toolbar-button {
  min-height: 28px;
  min-width: 32px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 13px;
  cursor: pointer;
}

.milkdown-markdown-editor__toolbar-button:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar-button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.milkdown-markdown-editor__file-input {
  display: none;
}

.milkdown-markdown-editor__content {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.milkdown-markdown-editor__milkdown,
.milkdown-markdown-editor__source {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.milkdown-markdown-editor__source {
  display: block;
  border: none;
  padding: 20px 24px;
  resize: none;
  outline: none;
  background: transparent;
  color: var(--el-text-color-primary);
  font: 14px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor__loading {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  background: color-mix(in srgb, var(--el-bg-color-overlay) 86%, transparent);
  backdrop-filter: blur(3px);
}

.milkdown-markdown-editor :deep(.milkdown) {
  height: 100%;
}

.milkdown-markdown-editor :deep(.ProseMirror) {
  height: 100%;
  min-height: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
  overflow: auto;
  outline: none;
  color: var(--el-text-color-primary);
  font-size: 15px;
  line-height: 1.75;
}

.milkdown-markdown-editor :deep(.ProseMirror p) {
  margin: 0 0 0.85em;
}

.milkdown-markdown-editor :deep(.ProseMirror h1),
.milkdown-markdown-editor :deep(.ProseMirror h2),
.milkdown-markdown-editor :deep(.ProseMirror h3),
.milkdown-markdown-editor :deep(.ProseMirror h4),
.milkdown-markdown-editor :deep(.ProseMirror h5),
.milkdown-markdown-editor :deep(.ProseMirror h6) {
  margin: 1.1em 0 0.55em;
  line-height: 1.32;
}

.milkdown-markdown-editor :deep(.ProseMirror h1:first-child),
.milkdown-markdown-editor :deep(.ProseMirror h2:first-child),
.milkdown-markdown-editor :deep(.ProseMirror h3:first-child) {
  margin-top: 0;
}

.milkdown-markdown-editor :deep(.ProseMirror blockquote) {
  margin: 1em 0;
  padding: 0.2em 0 0.2em 1em;
  border-left: 3px solid var(--el-color-primary);
  color: var(--el-text-color-secondary);
}

.milkdown-markdown-editor :deep(.ProseMirror pre) {
  overflow: auto;
  padding: 12px 14px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--el-bg-color));
}

.milkdown-markdown-editor :deep(.ProseMirror code) {
  border-radius: 4px;
  padding: 2px 4px;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--el-bg-color));
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor :deep(.ProseMirror pre code) {
  padding: 0;
  background: transparent;
}

.milkdown-markdown-editor :deep(.ProseMirror table) {
  width: max-content;
  max-width: 100%;
  border-collapse: collapse;
}

.milkdown-markdown-editor :deep(.ProseMirror th),
.milkdown-markdown-editor :deep(.ProseMirror td) {
  border: 1px solid var(--el-border-color);
  padding: 6px 8px;
}

.milkdown-markdown-editor :deep(.ProseMirror img) {
  max-width: 100%;
  border-radius: 8px;
}

.milkdown-markdown-editor :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
}

.milkdown-markdown-editor--dark {
  background: var(--el-bg-color-overlay);
}

@media (max-width: 768px) {
  .milkdown-markdown-editor {
    height: 560px;
  }

  .milkdown-markdown-editor__toolbar {
    align-items: stretch;
    gap: 8px;
  }

  .milkdown-markdown-editor__toolbar-group--tail {
    margin-left: 0;
  }

  .milkdown-markdown-editor :deep(.ProseMirror),
  .milkdown-markdown-editor__source {
    padding: 16px;
  }
}
</style>
