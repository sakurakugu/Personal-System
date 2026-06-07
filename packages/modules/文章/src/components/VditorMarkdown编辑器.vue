<script setup lang="ts">
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import '../styles/article-markdown.css'
import MarkdownMindmap from './Markdown思维导图.vue'
import { computed, createVNode, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, render, watch } from 'vue'
import { 增强文章Markdown } from '../composables/增强文章Markdown'
import { renderArticleMarkdown } from '../markdown'
import {
  创建Vditor文章编辑器选项,
  格式化Markdown图片,
  type Vditor表格尺寸,
  type VditorMermaid图表类型,
  type Vditor公式类型,
  type VditorMarkdownImagePayload as VditorMarkdown图片Payload,
  type VditorMarkdownImageUploader as VditorMarkdown图片Uploader,
} from '../markdown/vditor'
import { 构建VditorMermaid代码片段, 构建Vditor公式代码片段 } from '../markdown/vditor/snippets'

export type VditorMarkdownImagePayload = VditorMarkdown图片Payload
export type VditorMarkdownImageUploader = VditorMarkdown图片Uploader
export type Vditor右侧预览类型 = 'preview' | 'html' | 'mindmap'

export interface VditorMarkdown编辑器实例 {
  getMarkdown: () => string
  setMarkdown: (markdown: string) => void
  insertMarkdown: (markdown: string) => void
  getEditorView: () => null
  getScrollElement: () => HTMLElement | null
  getScrollRatio: () => number
  setScrollRatio: (ratio: number) => void
  focus: () => void
}

type Vditor内部状态 = {
  currentMode?: 'sv' | 'wysiwyg' | 'ir'
  ir?: { element?: HTMLElement }
  sv?: { element?: HTMLElement }
  wysiwyg?: { element?: HTMLElement }
  preview?: {
    element?: HTMLElement
    previewElement?: HTMLElement
    render?: (vditor: Vditor内部状态, value?: string) => void
  }
  element?: HTMLElement
}

type 带内部状态的Vditor = {
  destroy: () => void
  getValue: () => string
  setTheme: (theme: 'dark' | 'classic', contentTheme?: string, codeTheme?: string) => void
  setValue: (markdown: string, clearStack?: boolean) => void
  insertValue: (value: string, render?: boolean) => void
  insertMD: (md: string) => void
  updateValue: (value: string) => void
  updateToolbarConfig: (options: { pin: boolean }) => void
  getSelection: () => string
  focus: () => void
  vditor?: Vditor内部状态
}

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  theme?: 'light' | 'dark'
  previewType?: Vditor右侧预览类型
  previewTitle?: string
  uploadImages?: VditorMarkdownImageUploader
  formatContent?: () => void | Promise<unknown>
  fullscreenRootSelector?: string
  scrollSync?: boolean
  showScrollSync?: boolean
}>(), {
  placeholder: '在此编写 Markdown 内容...',
  theme: 'light',
  previewType: 'preview',
  previewTitle: '',
  uploadImages: undefined,
  formatContent: undefined,
  fullscreenRootSelector: '',
  scrollSync: true,
  showScrollSync: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  ready: []
  loadingChange: [value: boolean]
  uploadError: [error: unknown]
  modeChange: [sourceMode: boolean]
  'update:scrollSync': [value: boolean]
}>()

const rootRef = ref<HTMLDivElement | null>(null)
const vditorMountRef = ref<HTMLDivElement | null>(null)
const editor = ref<带内部状态的Vditor | null>(null)
const vueAppContext = getCurrentInstance()?.appContext
const fileInputRef = ref<HTMLInputElement | null>(null)
const cropFileInputRef = ref<HTMLInputElement | null>(null)
const loading = ref(true)
const isUploading = ref(false)
const lastMarkdown = ref(props.modelValue)
const isApplyingExternalMarkdown = ref(false)
const imageCropDialogVisible = ref(false)
const imageCropPreviewUrl = ref('')
const imageCropSourceFile = ref<File | null>(null)
const imageCropNaturalSize = ref({ width: 0, height: 0 })
const imageCropRect = ref({ x: 0.08, y: 0.08, width: 0.84, height: 0.84 })
const imageCropStageRef = ref<HTMLDivElement | null>(null)
const imageCropDragState = ref<{
  pointerId: number
  mode: 'move' | 'resize'
  startX: number
  startY: number
  startRect: typeof imageCropRect.value
} | null>(null)
const cursorStatus = ref({
  line: 1,
  selectedWords: 0,
  selectedCharacters: 0,
})
let customPreviewMountHost: HTMLDivElement | null = null

const rootClass = computed(() => ({
  'vditor-markdown-editor--dark': props.theme === 'dark',
  'vditor-markdown-editor--uploading': isUploading.value,
}))
const editorStats = computed(() => buildEditorStats(lastMarkdown.value))
const editorModeLabel = computed(() => {
  const mode = 获取当前编辑模式()
  if (mode === 'sv') return '源码预览'
  if (mode === 'wysiwyg') return '所见即所得'
  return '即时渲染'
})

let mutationObserver: MutationObserver | null = null
let statusUpdateTimer = 0

onMounted(() => {
  window.addEventListener('resize', handleWindowResize)
  mountVditor()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowResize)
  if (statusUpdateTimer) {
    window.clearTimeout(statusUpdateTimer)
    statusUpdateTimer = 0
  }
  mutationObserver?.disconnect()
  clearCustomPreviewMount()
  releaseImageCropPreviewUrl()
  安全销毁编辑器实例()
  editor.value = null
})

watch(
  () => props.modelValue,
  (value) => {
    if (value === lastMarkdown.value || isApplyingExternalMarkdown.value) {
      return
    }
    setMarkdown(value)
  },
)

watch(
  () => props.theme,
  (theme) => {
    editor.value?.setTheme(
      theme === 'dark' ? 'dark' : 'classic',
      theme === 'dark' ? 'dark' : 'light',
      theme === 'dark' ? 'native' : 'github',
    )
    refreshCustomPreview()
  },
)

watch(
  () => [props.previewType, props.previewTitle] as const,
  () => {
    refreshCustomPreview()
  },
)

watch(
  () => [props.showScrollSync, props.scrollSync, props.uploadImages] as const,
  () => {
    editor.value?.updateToolbarConfig({ pin: false })
  },
)

function mountVditor() {
  const mountElement = vditorMountRef.value
  if (!mountElement) {
    return
  }

  loading.value = true
  emit('loadingChange', true)

  editor.value = new Vditor(mountElement, 创建Vditor文章编辑器选项({
    value: props.modelValue,
    placeholder: props.placeholder,
    theme: props.theme,
    uploadImages: props.uploadImages,
    onInput: handleVditorInput,
    onKeydown: () => {
      scheduleCursorStatusUpdate()
    },
    onUploadError: (error) => emit('uploadError', error),
    onReady: handleVditorReady,
    toolbar: {
      showScrollSync: props.showScrollSync,
      scrollSync: props.scrollSync,
      canUpload: Boolean(props.uploadImages),
      onImageUpload: openImagePicker,
      onImageLink: insertImageLink,
      onImageCropUpload: openCropImagePicker,
      onInsertMermaid: insertMermaidSnippet,
      onInsertMath: insertMathSnippet,
      onUnderline: insertUnderline,
      onSubscript: insertSubscript,
      onSuperscript: insertSuperscript,
      onInsertTable: insertTable,
      onFormat: props.formatContent,
      onToggleScrollSync: () => emit('update:scrollSync', !props.scrollSync),
      onTogglePageFullscreen: togglePageFullscreen,
    },
  })) as unknown as 带内部状态的Vditor
}

function 安全销毁编辑器实例() {
  const currentEditor = editor.value
  if (!currentEditor) {
    return
  }

  try {
    const 编辑器状态 = currentEditor as unknown as 带内部状态的Vditor
    if (编辑器状态.vditor?.element) {
      currentEditor.destroy()
    }
  } catch (error) {
    console.warn('[文章编辑器] 销毁 Vditor 实例失败', error)
  }
}

function 获取当前编辑器实例(): 带内部状态的Vditor | null {
  const currentEditor = editor.value
  if (!currentEditor) {
    return null
  }

  return currentEditor.vditor ? currentEditor : null
}

function 获取当前编辑模式(): 'sv' | 'wysiwyg' | 'ir' | null {
  const currentEditor = editor.value
  if (!currentEditor) {
    return null
  }

  return currentEditor.vditor?.currentMode ?? null
}

function handleVditorReady() {
  installCustomPreviewRenderer()
  loading.value = false
  lastMarkdown.value = 获取当前编辑器实例()?.getValue() ?? props.modelValue
  emit('loadingChange', false)
  emit('ready')
  emit('modeChange', isSourceMode())
  updateCursorStatus()
  bindModeObserver()
  void nextTick(() => {
    bindTablePickerHoverState()
  })
}

function installCustomPreviewRenderer() {
  const currentEditor = 获取当前编辑器实例()
  const previewState = currentEditor?.vditor?.preview
  const previewElement = previewState?.previewElement
  if (!currentEditor || !previewState || !previewElement) {
    return
  }

  previewState.render = (_vditor, value) => {
    if (typeof value === 'string') {
      renderCustomPreview(previewElement, currentEditor.getValue(), value)
      return
    }

    renderCustomPreview(previewElement, currentEditor.getValue())
  }
  refreshCustomPreview(lastMarkdown.value)
}

function refreshCustomPreview(markdown?: string) {
  const currentEditor = 获取当前编辑器实例()
  const previewElement = currentEditor?.vditor?.preview?.previewElement
  if (!currentEditor || !previewElement) {
    return
  }

  renderCustomPreview(previewElement, markdown ?? currentEditor.getValue())
}

function renderCustomPreview(previewElement: HTMLElement, markdown: string, rawHtml?: string) {
  clearCustomPreviewMount()
  resetPreviewElementClasses(previewElement)

  const trimmedMarkdown = markdown.trim()
  if (!trimmedMarkdown) {
    previewElement.innerHTML = ''
    return
  }

  if (props.previewType === 'html') {
    renderHtmlPreview(previewElement, rawHtml ?? renderArticleMarkdown(markdown).html)
    return
  }

  if (props.previewType === 'mindmap') {
    renderMindmapPreview(previewElement, markdown)
    return
  }

  const rendered = renderArticleMarkdown(markdown)
  previewElement.classList.add('article-markdown-preview')
  previewElement.innerHTML = rendered.html
  增强文章Markdown(previewElement)
}

function clearCustomPreviewMount() {
  if (customPreviewMountHost) {
    render(null, customPreviewMountHost)
    customPreviewMountHost.remove()
    customPreviewMountHost = null
  }
}

function resetPreviewElementClasses(previewElement: HTMLElement) {
  const previewContainer = previewElement.closest<HTMLElement>('.vditor-preview')
  previewContainer?.classList.remove('vditor-markdown-editor__preview-container--mindmap')
  previewElement.classList.remove(
    'article-markdown-preview',
    'vditor-markdown-editor__html-preview',
    'vditor-markdown-editor__mindmap-preview',
  )
}

function renderHtmlPreview(previewElement: HTMLElement, html: string) {
  previewElement.classList.add('vditor-markdown-editor__html-preview')
  previewElement.innerHTML = `<pre class="vditor-markdown-editor__html-preview-content"><code>${escapeHtml(html)}</code></pre>`
}

function renderMindmapPreview(previewElement: HTMLElement, markdown: string) {
  const previewContainer = previewElement.closest<HTMLElement>('.vditor-preview')
  const previewHeight = getMindmapPreviewHeight(previewContainer, previewElement)
  const mindmapHeight = Math.max(320, previewHeight - 40)

  previewContainer?.classList.add('vditor-markdown-editor__preview-container--mindmap')
  previewElement.classList.add('vditor-markdown-editor__mindmap-preview')
  const host = document.createElement('div')
  host.className = 'vditor-markdown-editor__mindmap-host'
  host.style.height = `${mindmapHeight}px`
  previewElement.replaceChildren(host)
  customPreviewMountHost = host
  const vnode = createVNode(MarkdownMindmap, {
    content: markdown,
    title: props.previewTitle,
    height: mindmapHeight,
  })
  if (vueAppContext) {
    vnode.appContext = vueAppContext
  }
  render(vnode, host)
}

function getMindmapPreviewHeight(previewContainer: HTMLElement | null, previewElement: HTMLElement): number {
  const containerHeight = previewContainer?.clientHeight ?? 0
  if (containerHeight > 0) {
    return containerHeight
  }

  const elementHeight = previewElement.clientHeight
  if (elementHeight > 0) {
    return elementHeight
  }

  return 560
}

function handleWindowResize() {
  if (props.previewType !== 'mindmap') {
    return
  }

  refreshCustomPreview()
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function bindModeObserver() {
  mutationObserver?.disconnect()
  const root = rootRef.value
  if (!root) {
    return
  }

  mutationObserver = new MutationObserver(() => {
    emit('modeChange', isSourceMode())
    scheduleCursorStatusUpdate()
  })
  mutationObserver.observe(root, {
    attributes: true,
    childList: true,
    subtree: true,
    attributeFilter: ['class'],
  })
}

function handleVditorInput(value: string) {
  if (isApplyingExternalMarkdown.value) {
    return
  }

  lastMarkdown.value = value
  emit('update:modelValue', value)
  scheduleCursorStatusUpdate()
}

function getMarkdown(): string {
  const value = 获取当前编辑器实例()?.getValue() ?? lastMarkdown.value
  lastMarkdown.value = value
  return value
}

function setMarkdown(markdown: string) {
  lastMarkdown.value = markdown
  const currentEditor = 获取当前编辑器实例()
  if (!currentEditor) {
    return
  }

  isApplyingExternalMarkdown.value = true
  currentEditor.setValue(markdown, true)
  isApplyingExternalMarkdown.value = false
  refreshCustomPreview(markdown)
  scheduleCursorStatusUpdate()
}

function insertMarkdown(markdown: string) {
  if (!markdown) {
    return
  }

  const initializedEditor = 获取当前编辑器实例()
  if (!initializedEditor) {
    lastMarkdown.value += markdown
    emit('update:modelValue', lastMarkdown.value)
    return
  }

  initializedEditor.insertValue(markdown)
  lastMarkdown.value = initializedEditor.getValue()
  emit('update:modelValue', lastMarkdown.value)
  scheduleCursorStatusUpdate()
}

function insertUnderline() {
  insertInlineTag('u', '下划线文本')
}

function insertSubscript() {
  insertInlineTag('sub', '下标')
}

function insertSuperscript() {
  insertInlineTag('sup', '上标')
}

function insertInlineTag(tagName: 'u' | 'sub' | 'sup', fallbackText: string) {
  const initializedEditor = 获取当前编辑器实例()
  if (!initializedEditor) {
    insertMarkdown(`<${tagName}>${fallbackText}</${tagName}>`)
    return
  }

  const selectedText = initializedEditor.getSelection().trim()
  const content = selectedText || fallbackText
  const wrappedContent = `<${tagName}>${content}</${tagName}>`

  if (selectedText) {
    initializedEditor.updateValue(wrappedContent)
  } else {
    const cursorOffset = getApproximateCursorOffset()
    initializedEditor.insertValue(wrappedContent)
    restoreCursorOffset(cursorOffset + tagName.length + 2)
  }

  lastMarkdown.value = initializedEditor.getValue()
  emit('update:modelValue', lastMarkdown.value)
  scheduleCursorStatusUpdate()
}

function insertTable(size: Vditor表格尺寸) {
  const markdown = buildTableMarkdown(size)
  const currentEditor = 获取当前编辑器实例()
  if (!currentEditor) {
    insertMarkdown(markdown)
    return
  }

  currentEditor.insertMD(markdown)
  lastMarkdown.value = currentEditor.getValue()
  emit('update:modelValue', lastMarkdown.value)
  scheduleCursorStatusUpdate()
}

function insertMermaidSnippet(type: string) {
  insertMarkdown(构建VditorMermaid代码片段(type as VditorMermaid图表类型))
  focus()
}

function insertMathSnippet(type: Vditor公式类型) {
  insertMarkdown(构建Vditor公式代码片段(type))
  focus()
}

function getEditorView(): null {
  return null
}

function getScrollElement(): HTMLElement | null {
  const root = rootRef.value
  if (!root) {
    return null
  }

  return root.querySelector<HTMLElement>('.vditor-ir')
    ?? root.querySelector<HTMLElement>('.vditor-wysiwyg')
    ?? root.querySelector<HTMLElement>('.vditor-sv')
    ?? root.querySelector<HTMLElement>('.vditor-content')
}

function getScrollRatio(): number {
  const scrollElement = getScrollElement()
  if (!scrollElement) {
    return 0
  }

  const maxScrollTop = scrollElement.scrollHeight - scrollElement.clientHeight
  if (maxScrollTop <= 0) {
    return 0
  }

  return scrollElement.scrollTop / maxScrollTop
}

function setScrollRatio(ratio: number) {
  const scrollElement = getScrollElement()
  if (!scrollElement) {
    return
  }

  const normalizedRatio = Math.min(1, Math.max(0, ratio))
  const maxScrollTop = scrollElement.scrollHeight - scrollElement.clientHeight
  scrollElement.scrollTop = maxScrollTop <= 0 ? 0 : maxScrollTop * normalizedRatio
}

function focus() {
  获取当前编辑器实例()?.focus()
}

function isSourceMode(): boolean {
  return 获取当前编辑模式() === 'sv'
}

function scheduleCursorStatusUpdate() {
  if (statusUpdateTimer) {
    window.clearTimeout(statusUpdateTimer)
  }
  statusUpdateTimer = window.setTimeout(() => {
    statusUpdateTimer = 0
    updateCursorStatus()
  }, 30)
}

function updateCursorStatus() {
  const selection = window.getSelection()
  const selectedText = selection?.toString() ?? ''
  const cursorOffset = getApproximateCursorOffset()
  cursorStatus.value = buildCursorStatusFromOffsets(getMarkdown(), cursorOffset, cursorOffset + selectedText.length)
}

function getApproximateCursorOffset(): number {
  const scrollElement = getCurrentEditorElement()
  const selection = window.getSelection()
  if (!scrollElement || !selection || selection.rangeCount === 0) {
    return 0
  }

  const range = selection.getRangeAt(0)
  if (!scrollElement.contains(range.startContainer)) {
    return 0
  }

  const beforeRange = range.cloneRange()
  beforeRange.selectNodeContents(scrollElement)
  beforeRange.setEnd(range.startContainer, range.startOffset)
  return beforeRange.toString().length
}

function getCurrentEditorElement(): HTMLElement | null {
  const currentEditor = 获取当前编辑器实例()
  if (!currentEditor) {
    return getScrollElement()
  }

  const currentMode = 获取当前编辑模式()
  if (!currentMode) {
    return getScrollElement()
  }
  const vditorState = (currentEditor as unknown as 带内部状态的Vditor).vditor as Record<'sv' | 'wysiwyg' | 'ir', {
    element?: HTMLElement
  } | undefined>
  const modeState = vditorState[currentMode]
  return modeState?.element ?? getScrollElement()
}

function restoreCursorOffset(offset: number) {
  window.requestAnimationFrame(() => {
    const editorElement = getCurrentEditorElement()
    if (!editorElement) {
      return
    }

    focus()
    setSelectionByTextOffset(editorElement, offset)
    scheduleCursorStatusUpdate()
  })
}

function setSelectionByTextOffset(editorElement: HTMLElement, offset: number) {
  const normalizedOffset = Math.max(0, offset)
  const selection = window.getSelection()
  if (!selection) {
    return
  }

  const textNodes = collectEditorTextNodes(editorElement)
  const range = document.createRange()

  if (textNodes.length === 0) {
    range.setStart(editorElement, 0)
    range.collapse(true)
    selection.removeAllRanges()
    selection.addRange(range)
    return
  }

  let traversedLength = 0
  for (const textNode of textNodes) {
    const nextLength = traversedLength + textNode.textContent!.length
    if (normalizedOffset <= nextLength) {
      range.setStart(textNode, normalizedOffset - traversedLength)
      range.collapse(true)
      selection.removeAllRanges()
      selection.addRange(range)
      return
    }
    traversedLength = nextLength
  }

  const lastTextNode = textNodes[textNodes.length - 1]
  range.setStart(lastTextNode, lastTextNode.textContent!.length)
  range.collapse(true)
  selection.removeAllRanges()
  selection.addRange(range)
}

function collectEditorTextNodes(editorElement: HTMLElement): Text[] {
  const textNodes: Text[] = []
  const walker = document.createTreeWalker(editorElement, NodeFilter.SHOW_TEXT)
  let currentNode = walker.nextNode()
  while (currentNode) {
    if (currentNode instanceof Text) {
      textNodes.push(currentNode)
    }
    currentNode = walker.nextNode()
  }
  return textNodes
}

function bindTablePickerHoverState() {
  const pickerButton = rootRef.value?.querySelector<HTMLElement>('.article-vditor-table-picker > button')
  if (!pickerButton || pickerButton.dataset.hoverBound === 'true') {
    return
  }

  const updateTablePickerState = (row: number, col: number) => {
    const label = pickerButton.querySelector<HTMLElement>('[data-role="table-label"]')
    if (label) {
      label.textContent = `${row} x ${col}`
    }

    pickerButton.querySelectorAll<HTMLElement>('[data-row][data-col]').forEach((cell) => {
      const cellRow = Number(cell.dataset.row)
      const cellCol = Number(cell.dataset.col)
      const isActive = cellRow <= row && cellCol <= col
      cell.classList.toggle('is-active', isActive)
    })
  }

  const handlePreview = (event: Event) => {
    const target = event.target
    if (!(target instanceof HTMLElement)) {
      return
    }

    const cell = target.closest<HTMLElement>('[data-row][data-col]')
    if (!cell) {
      return
    }

    const row = Number(cell.dataset.row)
    const col = Number(cell.dataset.col)
    if (!Number.isInteger(row) || !Number.isInteger(col)) {
      return
    }

    updateTablePickerState(row, col)
  }

  pickerButton.dataset.hoverBound = 'true'
  pickerButton.addEventListener('pointerover', handlePreview)
  pickerButton.addEventListener('focusin', handlePreview)
  pickerButton.addEventListener('pointerleave', () => {
    updateTablePickerState(3, 3)
  })
  updateTablePickerState(3, 3)
}

function buildCursorStatusFromOffsets(markdown: string, startOffset: number, endOffset: number) {
  const normalizedStartOffset = Math.min(markdown.length, Math.max(0, startOffset))
  const normalizedEndOffset = Math.min(markdown.length, Math.max(0, endOffset))
  const selectionStart = Math.min(normalizedStartOffset, normalizedEndOffset)
  const selectionEnd = Math.max(normalizedStartOffset, normalizedEndOffset)
  const beforeCursor = markdown.slice(0, normalizedStartOffset).replace(/\r\n/g, '\n')
  const selectedText = markdown.slice(selectionStart, selectionEnd)

  return {
    line: beforeCursor.length === 0 ? 1 : beforeCursor.split('\n').length,
    selectedWords: countReadableWords(selectedText),
    selectedCharacters: Array.from(selectedText).length,
  }
}

function countReadableWords(text: string): number {
  const chineseCharacterCount = text.match(/[\u4e00-\u9fff]/g)?.length ?? 0
  const latinWordCount = text.match(/[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*/g)?.length ?? 0
  return chineseCharacterCount + latinWordCount
}

function buildEditorStats(markdown: string) {
  const normalizedMarkdown = markdown.replace(/\r\n/g, '\n')
  const lines = normalizedMarkdown.length === 0 ? 1 : normalizedMarkdown.split('\n').length
  const visibleText = normalizedMarkdown
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*]\([^)]+\)/g, '')
    .replace(/\[([^\]]+)]\([^)]+\)/g, '$1')
    .replace(/[#>*_~`[\]()|:-]/g, ' ')
  const chineseCharacterCount = visibleText.match(/[\u4e00-\u9fff]/g)?.length ?? 0
  const latinWordCount = visibleText.match(/[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*/g)?.length ?? 0

  return {
    lines,
    words: chineseCharacterCount + latinWordCount,
    characters: Array.from(markdown).length,
  }
}

function buildTableMarkdown(size: Vditor表格尺寸) {
  const header = `| ${Array.from({ length: size.col }, (_item, index) => `列 ${index + 1}`).join(' | ')} |`
  const separator = `| ${Array.from({ length: size.col }, () => '---').join(' | ')} |`
  const bodyRows = Array.from(
    { length: Math.max(1, size.row - 1) },
    () => `| ${Array.from({ length: size.col }, () => '').join(' | ')} |`,
  )
  return `\n${[header, separator, ...bodyRows].join('\n')}\n`
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

function insertImageLink() {
  const url = window.prompt('请输入图片地址')
  if (!url?.trim()) {
    return
  }

  const alt = window.prompt('请输入图片说明', '') ?? ''
  insertMarkdown(`\n![${escapeMarkdownImageAlt(alt)}](${url.trim()})\n`)
  focus()
}

function escapeMarkdownImageAlt(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/\[/g, '\\[')
    .replace(/\]/g, '\\]')
    .replace(/\r?\n/g, ' ')
    .trim()
}

function openCropImagePicker() {
  if (!props.uploadImages || isUploading.value) {
    return
  }

  cropFileInputRef.value?.click()
}

function handleCropFileInputChange(event: Event) {
  const input = event.target
  if (!(input instanceof HTMLInputElement)) {
    return
  }

  const file = Array.from(input.files ?? []).find((item) => item.type.startsWith('image/'))
  input.value = ''
  if (!file) {
    return
  }

  void loadImageCropFile(file)
}

async function loadImageCropFile(file: File) {
  releaseImageCropPreviewUrl()
  const previewUrl = URL.createObjectURL(file)
  const image = new window.Image()
  image.decoding = 'async'
  image.src = previewUrl

  try {
    await image.decode()
  } catch (error) {
    URL.revokeObjectURL(previewUrl)
    emit('uploadError', error)
    return
  }

  imageCropPreviewUrl.value = previewUrl
  imageCropSourceFile.value = file
  imageCropNaturalSize.value = {
    width: image.naturalWidth || 1,
    height: image.naturalHeight || 1,
  }
  resetImageCropRect()
  imageCropDialogVisible.value = true
}

function releaseImageCropPreviewUrl() {
  if (imageCropPreviewUrl.value) {
    URL.revokeObjectURL(imageCropPreviewUrl.value)
  }
  imageCropPreviewUrl.value = ''
}

function closeImageCropDialog() {
  imageCropDialogVisible.value = false
  imageCropSourceFile.value = null
  imageCropDragState.value = null
  releaseImageCropPreviewUrl()
}

function resetImageCropRect() {
  imageCropRect.value = {
    x: 0.08,
    y: 0.08,
    width: 0.84,
    height: 0.84,
  }
}

function startImageCropDrag(mode: 'move' | 'resize', event: PointerEvent) {
  const stage = imageCropStageRef.value
  if (!stage) {
    return
  }

  imageCropDragState.value = {
    pointerId: event.pointerId,
    mode,
    startX: event.clientX,
    startY: event.clientY,
    startRect: { ...imageCropRect.value },
  }
  stage.setPointerCapture(event.pointerId)
}

function updateImageCropDrag(event: PointerEvent) {
  const stage = imageCropStageRef.value
  const dragState = imageCropDragState.value
  if (!stage || !dragState || dragState.pointerId !== event.pointerId) {
    return
  }

  const stageRect = stage.getBoundingClientRect()
  const deltaX = stageRect.width <= 0 ? 0 : (event.clientX - dragState.startX) / stageRect.width
  const deltaY = stageRect.height <= 0 ? 0 : (event.clientY - dragState.startY) / stageRect.height
  const minSize = 0.06

  if (dragState.mode === 'move') {
    imageCropRect.value = {
      ...dragState.startRect,
      x: clampNumber(dragState.startRect.x + deltaX, 0, 1 - dragState.startRect.width),
      y: clampNumber(dragState.startRect.y + deltaY, 0, 1 - dragState.startRect.height),
    }
    return
  }

  const nextWidth = clampNumber(dragState.startRect.width + deltaX, minSize, 1 - dragState.startRect.x)
  const nextHeight = clampNumber(dragState.startRect.height + deltaY, minSize, 1 - dragState.startRect.y)
  imageCropRect.value = {
    ...dragState.startRect,
    width: nextWidth,
    height: nextHeight,
  }
}

function finishImageCropDrag(event: PointerEvent) {
  const stage = imageCropStageRef.value
  const dragState = imageCropDragState.value
  if (!stage || !dragState || dragState.pointerId !== event.pointerId) {
    return
  }

  if (stage.hasPointerCapture(event.pointerId)) {
    stage.releasePointerCapture(event.pointerId)
  }
  imageCropDragState.value = null
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

async function confirmImageCropUpload() {
  try {
    const croppedFile = await buildCroppedImageFile()
    if (!croppedFile) {
      return
    }

    closeImageCropDialog()
    await uploadAndInsertImages([croppedFile])
  } catch (error) {
    emit('uploadError', error)
  }
}

async function buildCroppedImageFile(): Promise<File | null> {
  const sourceFile = imageCropSourceFile.value
  if (!sourceFile || !imageCropPreviewUrl.value) {
    return null
  }

  const image = new window.Image()
  image.decoding = 'async'
  image.src = imageCropPreviewUrl.value
  await image.decode()

  const naturalSize = imageCropNaturalSize.value
  const crop = imageCropRect.value
  const sourceX = Math.round(crop.x * naturalSize.width)
  const sourceY = Math.round(crop.y * naturalSize.height)
  const sourceWidth = Math.max(1, Math.round(crop.width * naturalSize.width))
  const sourceHeight = Math.max(1, Math.round(crop.height * naturalSize.height))
  const canvas = document.createElement('canvas')
  canvas.width = sourceWidth
  canvas.height = sourceHeight

  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('canvas 上下文创建失败')
  }

  context.imageSmoothingEnabled = true
  context.imageSmoothingQuality = 'high'
  context.drawImage(image, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, sourceWidth, sourceHeight)

  const outputType = sourceFile.type === 'image/jpeg' ? 'image/jpeg' : 'image/png'
  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, outputType, 0.92)
  })
  if (!blob) {
    throw new Error('图片裁剪失败')
  }

  const extension = outputType === 'image/jpeg' ? 'jpg' : 'png'
  const baseName = sourceFile.name.replace(/\.[^.]+$/, '').trim() || 'cropped-image'
  return new File([blob], `${baseName}-cropped.${extension}`, { type: outputType })
}

function handleEditorPaste(event: ClipboardEvent) {
  const files = Array.from(event.clipboardData?.files ?? []).filter((file) => file.type.startsWith('image/'))
  if (files.length === 0) {
    return
  }

  event.preventDefault()
  event.stopPropagation()
  void uploadAndInsertImages(files)
}

function handleEditorDrop(event: DragEvent) {
  const files = Array.from(event.dataTransfer?.files ?? []).filter((file) => file.type.startsWith('image/'))
  if (files.length === 0) {
    return
  }

  event.preventDefault()
  event.stopPropagation()
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
      .map((image) => 格式化Markdown图片(image))
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

function getFullscreenRoot(): HTMLElement | null {
  const root = rootRef.value
  if (!(root instanceof HTMLElement)) {
    return null
  }

  if (!props.fullscreenRootSelector) {
    return root
  }

  const fullscreenRoot = root.closest(props.fullscreenRootSelector)
  return fullscreenRoot instanceof HTMLElement ? fullscreenRoot : root
}

function togglePageFullscreen() {
  const root = getFullscreenRoot()
  if (!(root instanceof HTMLElement)) {
    return
  }

  root.classList.toggle('vditor-markdown-editor--page-fullscreen')
  void nextTick(() => {
    root.scrollIntoView({ block: 'nearest' })
    window.dispatchEvent(new Event('resize'))
  })
}

defineExpose<VditorMarkdown编辑器实例>({
  getMarkdown,
  setMarkdown,
  insertMarkdown,
  getEditorView,
  getScrollElement,
  getScrollRatio,
  setScrollRatio,
  focus,
})
</script>

<template>
  <div
    ref="rootRef"
    class="vditor-markdown-editor"
    :class="rootClass"
    @paste.capture="handleEditorPaste"
    @drop.capture="handleEditorDrop"
  >
    <div ref="vditorMountRef" class="vditor-markdown-editor__mount" />

    <button
      v-if="props.uploadImages"
      class="vditor-markdown-editor__hidden-action"
      type="button"
      tabindex="-1"
      aria-hidden="true"
      @click="openImagePicker"
    />
    <input
      ref="fileInputRef"
      class="vditor-markdown-editor__file-input"
      type="file"
      accept="image/*"
      multiple
      @change="handleFileInputChange"
    >
    <input
      ref="cropFileInputRef"
      class="vditor-markdown-editor__file-input"
      type="file"
      accept="image/*"
      @change="handleCropFileInputChange"
    >

    <div v-if="loading" class="vditor-markdown-editor__loading">
      正在加载编辑器...
    </div>

    <div class="vditor-markdown-editor__footer">
      <div class="vditor-markdown-editor__footer-left">
        <span class="vditor-markdown-editor__footer-item">{{ editorModeLabel }}</span>
        <span class="vditor-markdown-editor__footer-item">第 {{ cursorStatus.line }} 行</span>
        <span v-if="cursorStatus.selectedCharacters > 0" class="vditor-markdown-editor__footer-item">
          已选 {{ cursorStatus.selectedCharacters }} 字符 / {{ cursorStatus.selectedWords }} 词
        </span>
      </div>
      <div class="vditor-markdown-editor__footer-right">
        <span class="vditor-markdown-editor__footer-item">{{ editorStats.lines }} 行</span>
        <span class="vditor-markdown-editor__footer-item">{{ editorStats.words }} 词</span>
        <span class="vditor-markdown-editor__footer-item">{{ editorStats.characters }} 字符</span>
        <span v-if="isUploading" class="vditor-markdown-editor__footer-item">图片上传中...</span>
      </div>
    </div>

    <div v-if="imageCropDialogVisible" class="vditor-markdown-editor__crop-dialog">
      <div class="vditor-markdown-editor__crop-panel">
        <div class="vditor-markdown-editor__crop-header">
          <strong>裁剪图片</strong>
          <button class="vditor-markdown-editor__crop-close" type="button" @click="closeImageCropDialog">
            关闭
          </button>
        </div>
        <div class="vditor-markdown-editor__crop-stage">
          <div
            ref="imageCropStageRef"
            class="vditor-markdown-editor__crop-frame"
            @pointermove.prevent="updateImageCropDrag"
            @pointerup.prevent="finishImageCropDrag"
            @pointercancel.prevent="finishImageCropDrag"
          >
            <img
              class="vditor-markdown-editor__crop-image"
              :src="imageCropPreviewUrl"
              alt=""
              draggable="false"
            >
            <div
              class="vditor-markdown-editor__crop-rect"
              :style="{
                left: `${imageCropRect.x * 100}%`,
                top: `${imageCropRect.y * 100}%`,
                width: `${imageCropRect.width * 100}%`,
                height: `${imageCropRect.height * 100}%`,
              }"
              @pointerdown.prevent="startImageCropDrag('move', $event)"
            >
              <span class="vditor-markdown-editor__crop-rect-handle" @pointerdown.stop.prevent="startImageCropDrag('resize', $event)" />
            </div>
          </div>
        </div>
        <div class="vditor-markdown-editor__crop-footer">
          <span>{{ imageCropNaturalSize.width }} x {{ imageCropNaturalSize.height }}</span>
          <div class="vditor-markdown-editor__crop-actions">
            <button type="button" @click="resetImageCropRect">重置</button>
            <button class="is-primary" type="button" :disabled="isUploading" @click="confirmImageCropUpload">
              裁剪并上传
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vditor-markdown-editor {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 720px;
  min-height: 360px;
  overflow: visible;
  border: 1px solid color-mix(in srgb, var(--el-border-color) 72%, transparent);
  border-radius: 8px;
  background: var(--vditor-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--vditor-markdown-editor-bg-color, var(--el-bg-color-overlay));
}

.vditor-markdown-editor__mount {
  flex: 1 1 auto;
  min-height: 0;
}

.vditor-markdown-editor__mount :deep(.vditor) {
  height: 100% !important;
  border: none;
  border-radius: 0;
  background: transparent;
}

.vditor-markdown-editor__mount :deep(.vditor-content) {
  min-height: 0;
}

.vditor-markdown-editor__mount :deep(.vditor-ir),
.vditor-markdown-editor__mount :deep(.vditor-wysiwyg),
.vditor-markdown-editor__mount :deep(.vditor-sv) {
  color: var(--el-text-color-primary);
}

.vditor-markdown-editor__mount :deep(.vditor-toolbar),
.vditor-markdown-editor__mount :deep(.vditor-preview) {
  background: var(--vditor-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
}

.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__html-preview),
.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__mindmap-preview) {
  box-sizing: border-box;
  min-height: 100%;
  padding: 20px 24px;
}

.vditor-markdown-editor__mount :deep(.vditor-preview.vditor-markdown-editor__preview-container--mindmap) {
  overflow: hidden;
}

.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__mindmap-preview) {
  overflow: hidden;
}

.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__mindmap-host) {
  width: 100%;
  max-width: 100%;
}

.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__html-preview-content) {
  min-height: 100%;
  margin: 0;
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__html-preview-content code) {
  display: block;
  background: transparent;
  color: inherit;
}

.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__mindmap-host > .markdown-mindmap),
.vditor-markdown-editor__mount :deep(.vditor-markdown-editor__mindmap-preview > .markdown-mindmap) {
  min-height: 0;
  height: 100%;
  border: none;
  border-radius: 0;
}

.vditor-markdown-editor__mount :deep(.vditor-toolbar) {
  position: relative;
  z-index: 8;
  overflow: visible;
}

.vditor-markdown-editor__mount :deep(.vditor-hint),
.vditor-markdown-editor__mount :deep(.vditor-panel) {
  z-index: 24;
}

.vditor-markdown-editor__mount :deep(.article-vditor-image-menu-item) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 104px;
}

.vditor-markdown-editor__mount :deep(.article-vditor-lucide-icon) {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  fill: none !important;
  stroke: currentColor !important;
  stroke-width: 2 !important;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.vditor-markdown-editor__mount :deep(.article-vditor-image-menu-item .article-vditor-lucide-icon) {
  width: 14px;
  height: 14px;
}

.vditor-markdown-editor__mount :deep(.article-vditor-text-icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-toolbar > .vditor-hint) {
  min-width: 184px;
  padding: 10px;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker) {
  width: 100%;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker > button) {
  display: block;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: default;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker__content) {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker__label) {
  display: block;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker__grid) {
  display: grid;
  grid-template-columns: repeat(6, 18px);
  gap: 4px;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker__cell) {
  display: block;
  width: 18px;
  height: 18px;
  box-sizing: border-box;
  border: 1px solid color-mix(in srgb, var(--el-border-color) 82%, transparent);
  border-radius: 4px;
  background: color-mix(in srgb, var(--el-fill-color-light) 78%, transparent);
  cursor: pointer;
  transition: background-color 0.16s ease, border-color 0.16s ease;
}

.vditor-markdown-editor__mount :deep(.article-vditor-table-picker__cell.is-active) {
  border-color: color-mix(in srgb, var(--el-color-primary) 88%, transparent);
  background: color-mix(in srgb, var(--el-color-primary-light-7) 92%, transparent);
}

.vditor-markdown-editor__file-input,
.vditor-markdown-editor__hidden-action {
  display: none;
}

.vditor-markdown-editor__loading {
  position: absolute;
  inset: 0 0 24px;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  background: color-mix(in srgb, var(--el-bg-color-overlay) 86%, transparent);
  backdrop-filter: blur(3px);
}

.vditor-markdown-editor__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 24px;
  padding: 0 10px;
  box-sizing: border-box;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 72%, transparent);
  background: var(--vditor-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1;
}

.vditor-markdown-editor__footer-left,
.vditor-markdown-editor__footer-right {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.vditor-markdown-editor__footer-right {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.vditor-markdown-editor__footer-item {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  white-space: nowrap;
}

.vditor-markdown-editor__crop-dialog {
  position: fixed;
  inset: 0;
  z-index: 4100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  background: rgba(15, 23, 42, 0.48);
}

.vditor-markdown-editor__crop-panel {
  display: flex;
  flex-direction: column;
  width: min(860px, 100%);
  max-height: min(720px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.vditor-markdown-editor__crop-header,
.vditor-markdown-editor__crop-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.vditor-markdown-editor__crop-footer {
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.vditor-markdown-editor__crop-stage {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  max-height: 520px;
  padding: 16px;
  box-sizing: border-box;
  overflow: hidden;
  background:
    linear-gradient(45deg, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 25%, transparent 25%),
    linear-gradient(-45deg, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 75%),
    linear-gradient(-45deg, transparent 75%, color-mix(in srgb, var(--el-fill-color) 82%, transparent) 75%);
  background-position: 0 0, 0 10px, 10px -10px, -10px 0;
  background-size: 20px 20px;
}

.vditor-markdown-editor__crop-frame {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  max-height: 488px;
  touch-action: none;
}

.vditor-markdown-editor__crop-image {
  display: block;
  max-width: 100%;
  max-height: 488px;
  user-select: none;
}

.vditor-markdown-editor__crop-rect {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid var(--el-color-primary);
  background: rgba(64, 158, 255, 0.12);
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.38);
  cursor: move;
}

.vditor-markdown-editor__crop-rect-handle {
  position: absolute;
  right: -7px;
  bottom: -7px;
  width: 14px;
  height: 14px;
  box-sizing: border-box;
  border: 2px solid #fff;
  border-radius: 50%;
  background: var(--el-color-primary);
  cursor: nwse-resize;
}

.vditor-markdown-editor__crop-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vditor-markdown-editor__crop-close,
.vditor-markdown-editor__crop-actions button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.vditor-markdown-editor__crop-actions button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}

.vditor-markdown-editor__crop-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.vditor-markdown-editor--page-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 3000;
  width: 100vw !important;
  height: 100dvh !important;
  min-height: 0;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

@media (max-width: 768px) {
  .vditor-markdown-editor {
    height: 560px;
  }

  .vditor-markdown-editor__footer {
    align-items: flex-start;
    flex-direction: column;
    gap: 0;
    padding: 2px 10px;
  }

  .vditor-markdown-editor__footer-right {
    justify-content: flex-start;
  }
}
</style>
