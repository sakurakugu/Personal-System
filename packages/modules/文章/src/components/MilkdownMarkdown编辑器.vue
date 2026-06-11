<script setup lang="ts">
import {
  commandsCtx,
  defaultValueCtx,
  Editor,
  editorViewCtx,
  parserCtx,
  rootCtx,
  serializerCtx,
} from '@milkdown/core'
import type { MilkdownPlugin } from '@milkdown/ctx'
import { clipboard } from '@milkdown/plugin-clipboard'
import { cursor } from '@milkdown/plugin-cursor'
import { history } from '@milkdown/plugin-history'
import { indent } from '@milkdown/plugin-indent'
import { listener, listenerCtx } from '@milkdown/plugin-listener'
import { trailing } from '@milkdown/plugin-trailing'
import {
  commands as commonmarkCommands,
  keymap as commonmarkKeymap,
  plugins as commonmarkPlugins,
  schema as commonmarkSchema,
  createCodeBlockCommand,
  createCodeBlockInputRule,
  emphasisStarInputRule,
  emphasisUnderscoreInputRule,
  inlineCodeInputRule,
  insertHrCommand,
  linkSchema,
  listItemSchema,
  strongInputRule,
  toggleEmphasisCommand,
  toggleInlineCodeCommand,
  toggleLinkCommand,
  toggleStrongCommand,
  wrapInBlockquoteCommand,
  wrapInBlockquoteInputRule,
  wrapInBulletListCommand,
  wrapInBulletListInputRule,
  wrapInHeadingCommand,
  wrapInHeadingInputRule,
  wrapInOrderedListCommand,
  wrapInOrderedListInputRule,
} from '@milkdown/preset-commonmark'
import { gfm, insertTableCommand, toggleStrikethroughCommand } from '@milkdown/preset-gfm'
import { redo, undo } from '@milkdown/prose/history'
import { InputRule } from '@milkdown/prose/inputrules'
import type { MarkType } from '@milkdown/prose/model'
import { Plugin, TextSelection } from '@milkdown/prose/state'
import type { EditorView } from '@milkdown/prose/view'
import { $inputRule, $prose, insert, replaceAll } from '@milkdown/utils'
import fullEmojiMap from 'markdown-it-emoji/lib/data/full.mjs'
import lightEmojiMap from 'markdown-it-emoji/lib/data/light.mjs'
import emojiShortcutsMap from 'markdown-it-emoji/lib/data/shortcuts.mjs'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  buildCodeSyntaxSnippet,
  buildCustomMarkdownSnippet,
  buildGithubAlertSyntaxSnippet,
  buildMermaidSnippet,
  normalizeCustomMarkdownSnippet,
} from './MilkdownMarkdown编辑器/Markdown自定义语法片段'
import { buildExtendedMarkdownDecorations } from './MilkdownMarkdown编辑器/MilkdownMarkdown扩展装饰'
import {
  configureMarkdownSerializer,
  highlightMarkdownPlugins,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown标记语法'
import MilkdownMarkdown图片裁剪弹窗 from './MilkdownMarkdown编辑器/MilkdownMarkdown图片裁剪弹窗.vue'
import { normalizeSerializedMarkdown } from './MilkdownMarkdown编辑器/MilkdownMarkdown序列化'
import {
  GitHub卡片语法名称,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown语法常量'
import {
  createMarkdownKeyboardPlugin,
  isMarkdownStrongShortcut,
} from './MilkdownMarkdown编辑器/MilkdownMarkdown快捷键'
import MilkdownMarkdown编辑器底部状态栏 from './MilkdownMarkdown编辑器/MilkdownMarkdown编辑器底部状态栏.vue'
import { 使用MilkdownMarkdown图片上传 } from './MilkdownMarkdown编辑器/使用MilkdownMarkdown图片上传'
import MilkdownMarkdown工具栏 from './MilkdownMarkdown工具栏/MilkdownMarkdown工具栏.vue'
import { 创建MilkdownMarkdown工具栏项 } from './MilkdownMarkdown工具栏/创建MilkdownMarkdown工具栏项'
import type {
  ToolbarAction,
  ToolbarItem,
  ToolbarOverflowMenuEntry,
} from './MilkdownMarkdown工具栏/MilkdownMarkdown工具栏类型'
import { 使用MilkdownMarkdown工具栏折叠 } from './MilkdownMarkdown工具栏/使用MilkdownMarkdown工具栏折叠'
import { 使用MilkdownMarkdown工具栏菜单 } from './MilkdownMarkdown工具栏/使用MilkdownMarkdown工具栏菜单'

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
  formatMarkdown: () => string | null
  insertMarkdown: (markdown: string) => void
  getEditorView: () => EditorView | null
  getScrollElement: () => HTMLElement | null
  getScrollRatio: () => number
  setScrollRatio: (ratio: number) => void
  scrollToHeading: (headingIndex: number, sourceLine: number) => boolean
  redo: () => boolean
  focus: () => void
}

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  theme?: 'light' | 'dark'
  uploadImages?: MilkdownMarkdownImageUploader
  formatContent?: () => void | Promise<unknown>
  fullscreenRootSelector?: string
  scrollSync?: boolean
  showScrollSync?: boolean
  previewEnabled?: boolean
  previewLayoutMode?: 'split' | 'full'
  previewType?: 'preview' | 'html' | 'mindmap'
  showPreviewToggle?: boolean
  outlineVisible?: boolean
  showOutlineToggle?: boolean
}>(), {
  placeholder: '在此编写 Markdown 内容...',
  theme: 'light',
  uploadImages: undefined,
  formatContent: undefined,
  fullscreenRootSelector: '',
  scrollSync: true,
  showScrollSync: false,
  previewEnabled: false,
  previewLayoutMode: 'split',
  previewType: 'preview',
  showPreviewToggle: false,
  outlineVisible: false,
  showOutlineToggle: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  ready: []
  loadingChange: [value: boolean]
  uploadError: [error: unknown]
  modeChange: [sourceMode: boolean]
  'update:scrollSync': [value: boolean]
  'update:previewEnabled': [value: boolean]
  'update:previewLayoutMode': [value: 'split' | 'full']
  'update:previewType': [value: 'preview' | 'html' | 'mindmap']
  'update:outlineVisible': [value: boolean]
}>()

const rootRef = ref<HTMLDivElement | null>(null)
const toolbarRef = ref<InstanceType<typeof MilkdownMarkdown工具栏> | null>(null)
const sourceTextareaRef = ref<HTMLTextAreaElement | null>(null)
const editor = ref<Editor | null>(null)
const hoveredTableRows = ref(3)
const hoveredTableCols = ref(3)
const tableDialogVisible = ref(false)
const tableDialogRows = ref(8)
const tableDialogCols = ref(8)
const tableDialogRowsInputRef = ref<HTMLInputElement | null>(null)
const emojiPickerMode = ref<'emoji' | 'kaomoji'>('emoji')
const emojiDialogVisible = ref(false)
const loading = ref(true)
const isSourceMode = ref(false)
const sourceContent = ref('')
const lastMarkdown = ref(props.modelValue)
const isApplyingExternalMarkdown = ref(false)
const isEditorReadyForLocalUpdates = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const cropFileInputRef = ref<HTMLInputElement | null>(null)
const syntaxDialogVisible = ref(false)
const syntaxDialogTitle = ref('')
const syntaxDialogContent = ref('')
const githubCardDialogVisible = ref(false)
const githubCardRepoInputRef = ref<HTMLInputElement | null>(null)
const githubCardRepoInput = ref('')
const githubCardRepoError = ref('')
const cursorStatus = ref({
  line: 1,
  selectedWords: 0,
  selectedCharacters: 0,
})
let pendingScrollRatioAfterModeSwitch: number | null = null

const commonmarkEditorPlugins: MilkdownPlugin[] = [
  commonmarkSchema,
  [
    wrapInBlockquoteInputRule,
    wrapInBulletListInputRule,
    wrapInOrderedListInputRule,
    createCodeBlockInputRule,
    wrapInHeadingInputRule,
  ],
  [
    emphasisStarInputRule,
    emphasisUnderscoreInputRule,
    inlineCodeInputRule,
    strongInputRule,
  ],
  commonmarkCommands,
  $prose((ctx) => createMarkdownKeyboardPlugin(
    ctx.get(parserCtx),
    listItemSchema.type(ctx),
    {
      toggleStrong: () => ctx.get(commandsCtx).call(toggleStrongCommand.key),
    },
  )),
  commonmarkKeymap,
  commonmarkPlugins,
].flat()

const markdownLinkInputRule = $inputRule((ctx) => new InputRule(
  /\[([^\]\n]+)]\((https?:\/\/[^\s)]+)\)$/,
  (state, match, start, end) => {
    const linkText = match[1]
    const href = match[2]
    if (!linkText || !href) {
      return null
    }

    const linkMark = linkSchema.type(ctx).create({ href, title: null })
    const tr = state.tr.insertText(linkText, start, end)
    tr.addMark(start, start + linkText.length, linkMark)
    tr.removeStoredMark(linkSchema.type(ctx))
    return tr
  },
))
const reverseInlineMarkdownInput = $prose(() => new Plugin({
  props: {
    handleTextInput(view, from, to, text) {
      return handleReverseInlineMarkdownInput(view, from, to, text)
    },
  },
}))
const taskListCheckboxClickPlugin = $prose(() => new Plugin({
  props: {
    handleClickOn(view, _pos, node, nodePos, event) {
      if (node.type.name !== 'list_item' || node.attrs.checked == null) {
        return false
      }

      if (!isTaskListCheckboxClick(view, nodePos, event)) {
        return false
      }

      const checked = node.attrs.checked !== true
      view.dispatch(view.state.tr.setNodeMarkup(nodePos, undefined, {
        ...node.attrs,
        checked,
      }))
      return true
    },
  },
}))
const extendedMarkdownPreviewDecoration = $prose(() => new Plugin({
  props: {
    decorations(state) {
      return buildExtendedMarkdownDecorations(state.doc)
    },
  },
}))
const editorStatusPlugin = $prose(() => new Plugin({
  view() {
    return {
      update() {
        updateCursorStatus()
      },
    }
  },
}))
type ReverseInlineMarkdownRule = {
  delimiter: '*' | '**' | '`'
  markName: 'strong' | 'emphasis' | 'inlineCode'
  attrs?: Record<string, string>
}

type ReverseInlineMarkdownMatch = {
  contentStart: number
  contentEnd: number
  openingStart: number
  openingEnd: number
  closingStart: number
  closingEnd: number
  markType: MarkType
  attrs?: Record<string, string>
}

const 反向行内Markdown规则: ReverseInlineMarkdownRule[] = [
  { delimiter: '**', markName: 'strong', attrs: { marker: '*' } },
  { delimiter: '*', markName: 'emphasis', attrs: { marker: '*' } },
  { delimiter: '`', markName: 'inlineCode' },
]

const 表格行列选项 = [1, 2, 3, 4, 5, 6]
const 更多表格最大行列 = 20
const 常用Emoji存储键 = 'personal-system:article:markdown-editor:common-emojis'
const 常用颜文字存储键 = 'personal-system:article:markdown-editor:common-kaomoji'
const 常用Emoji最大数量 = 16
const 常用颜文字最大数量 = 8
const 默认常用Emoji短码 = [
  'smile',
  'joy',
  'rofl',
  'wink',
  'thinking',
  'neutral_face',
  'sob',
  'heart',
  'thumbsup',
  'clap',
  'fire',
  'tada',
  'rocket',
  'warning',
  'x',
  'white_check_mark',
]
const 默认常用颜文字 = [
  ':)',
  ':D',
  ';)',
  ':P',
  ':(',
  ":'(",
  '<3',
  '>:(',
]
const 全量Emoji选项 = Object.entries(fullEmojiMap).map(([shortcode, emoji]) => ({
  shortcode,
  emoji,
}))
const 轻量Emoji选项 = Object.entries(lightEmojiMap).map(([shortcode, emoji]) => ({
  shortcode,
  emoji,
}))
const 颜文字选项 = Object.entries(emojiShortcutsMap)
  .flatMap(([shortcode, shortcuts]) => shortcuts.map((shortcut) => ({
    shortcode,
    shortcut,
    emoji: fullEmojiMap[shortcode] ?? '',
  })))
const 颜文字快捷值集合 = new Set(颜文字选项.map((option) => option.shortcut))
const 常用Emoji短码 = ref<string[]>([])
const 常用颜文字 = ref<string[]>([])
const 常用Emoji选项 = computed(() => 常用Emoji短码.value
  .map((shortcode) => {
    const emoji = fullEmojiMap[shortcode]
    return emoji ? { shortcode, emoji } : null
  })
  .filter((item): item is { shortcode: string; emoji: string } => Boolean(item)))
const 常用颜文字选项 = computed(() => 常用颜文字.value
  .map((shortcut) => 颜文字选项.find((option) => option.shortcut === shortcut))
  .filter((item): item is { shortcode: string; shortcut: string; emoji: string } => Boolean(item)))
const {
  isUploading,
  imageCropDialogVisible,
  imageCropPreviewUrl,
  imageCropNaturalSize,
  imageCropRect,
  openImagePicker,
  handleFileInputChange,
  insertImageLink,
  openCropImagePicker,
  handleCropFileInputChange,
  releaseImageCropPreviewUrl,
  closeImageCropDialog,
  resetImageCropRect,
  confirmImageCropUpload,
  handleEditorPaste,
  handleEditorDrop,
} = 使用MilkdownMarkdown图片上传({
  fileInputRef,
  cropFileInputRef,
  获取上传图片函数: () => props.uploadImages,
  插入Markdown: (markdown) => insertMarkdown(markdown),
  聚焦编辑器: () => focus(),
  报告上传错误: (error) => emit('uploadError', error),
})

const toolbarItems = 创建MilkdownMarkdown工具栏项({
  isUploading: () => isUploading.value,
  isSourceMode: () => isSourceMode.value,
  hasFormatContent: () => Boolean(props.formatContent),
  showScrollSync: () => props.showScrollSync,
  scrollSync: () => props.scrollSync,
  previewEnabled: () => props.previewEnabled,
  previewLayoutMode: () => props.previewLayoutMode,
  previewType: () => props.previewType,
  showPreviewToggle: () => props.showPreviewToggle,
  outlineVisible: () => props.outlineVisible,
  showOutlineToggle: () => props.showOutlineToggle,
})
const {
  toolbarOverflowCount,
  工具栏更多键,
  工具栏公式索引,
  工具栏折叠候选索引,
  shouldShowToolbarItem,
  shouldShowToolbarSeparator,
  初始化工具栏折叠监听,
  清理工具栏折叠监听,
  调度工具栏折叠更新,
} = 使用MilkdownMarkdown工具栏折叠({
  toolbarItems,
  getToolbarElement: 获取工具栏滚动元素,
  getRootElement: () => rootRef.value,
})
const {
  activeDropdownKey,
  activeDropdownStyle,
  activeOverflowSubmenuKey,
  toggleToolbarDropdown,
  openToolbarDropdown,
  toggleToolbarMoreDropdown,
  openToolbarMoreDropdown,
  handleToolbarOverflowMenuClick,
  openToolbarOverflowSubmenu,
  handleToolbarOverflowSubmenuClick,
  closeToolbarDropdown,
  handleDocumentPointerDown,
} = 使用MilkdownMarkdown工具栏菜单({
  moreKey: 工具栏更多键,
  getToolbarItemKey,
  runAction: runToolbarAction,
})
const 溢出工具栏菜单项 = computed<ToolbarOverflowMenuEntry[]>(() => {
  const entries: ToolbarOverflowMenuEntry[] = []
  const overflowIndexes = 工具栏折叠候选索引.value.slice(0, toolbarOverflowCount.value).reverse()

  for (const itemIndex of overflowIndexes) {
    const item = toolbarItems[itemIndex]
    if (!item) {
      continue
    }

    const icon = getToolbarIcon(item)
    if (!item.action) {
      continue
    }

    entries.push({
      kind: 'option',
      key: `${itemIndex}-${item.action}-${item.payload ?? item.label}`,
      label: item.label,
      title: getToolbarTitle(item),
      action: item.action,
      payload: item.payload,
      icon,
      disabled: item.disabled,
      children: item.dropdown?.map((option, optionIndex) => ({
        ...option,
        key: `${itemIndex}-${option.kind ?? 'option'}-${optionIndex}-${option.label}`,
      })),
    })
  }

  return entries
})
const currentMarkdown = computed(() => (isSourceMode.value ? sourceContent.value : lastMarkdown.value))
const editorStats = computed(() => buildEditorStats(currentMarkdown.value))
const editorModeLabel = computed(() => (isSourceMode.value ? '源码' : '所见即所得'))
const rootClass = computed(() => ({
  'milkdown-markdown-editor--dark': props.theme === 'dark',
  'milkdown-markdown-editor--source': isSourceMode.value,
  'milkdown-markdown-editor--uploading': isUploading.value,
}))
const 表格基础语法说明 = [
  '| 左对齐 | 居中对齐 | 右对齐 | 默认 |',
  '| :-- | :--: | --: | --- |',
  '| 内容 | 内容 | 内容 | 内容 |',
  '',
  ':-- 表示左对齐',
  ':--: 表示居中对齐',
  '--: 表示右对齐',
  '--- 表示正常的标题和内容的分隔线',
].join('\n')

function getToolbarIcon(item: ToolbarItem) {
  return item.dynamicIcon?.() ?? item.icon
}

function getToolbarTitle(item: ToolbarItem) {
  return item.dynamicTitle?.() ?? item.title
}

function 获取工具栏滚动元素(): HTMLDivElement | null {
  return toolbarRef.value?.getScrollElement() ?? null
}

function 读取本地字符串列表(storageKey: string, fallback: string[]): string[] {
  if (typeof window === 'undefined') {
    return [...fallback]
  }

  try {
    const rawValue = window.localStorage.getItem(storageKey)
    const value = rawValue ? JSON.parse(rawValue) : fallback
    if (!Array.isArray(value)) {
      return [...fallback]
    }

    const result = value.filter((item): item is string => typeof item === 'string')
    return result.length > 0 ? result : [...fallback]
  } catch (error) {
    console.warn('读取 Markdown 编辑器常用表情失败', error)
    return [...fallback]
  }
}

function 写入本地字符串列表(storageKey: string, value: string[]) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(storageKey, JSON.stringify(value))
  } catch (error) {
    console.warn('保存 Markdown 编辑器常用表情失败', error)
  }
}

function 初始化常用表情记录() {
  常用Emoji短码.value = 合并默认常用项(
    读取本地字符串列表(常用Emoji存储键, 默认常用Emoji短码),
    默认常用Emoji短码,
  )
    .filter((shortcode) => Boolean(fullEmojiMap[shortcode]))
    .slice(0, 常用Emoji最大数量)
  常用颜文字.value = 合并默认常用项(
    读取本地字符串列表(常用颜文字存储键, 默认常用颜文字),
    默认常用颜文字,
  )
    .filter((shortcut) => 颜文字快捷值集合.has(shortcut))
    .slice(0, 常用颜文字最大数量)
}

function 合并默认常用项(value: string[], fallback: string[]): string[] {
  return [...value, ...fallback.filter((item) => !value.includes(item))]
}

function 更新最近使用项(value: string, currentValues: string[], maxLength: number): string[] {
  return [value, ...currentValues.filter((item) => item !== value)].slice(0, maxLength)
}

function 记录常用Emoji(shortcode: string) {
  if (!fullEmojiMap[shortcode]) {
    return
  }

  常用Emoji短码.value = 更新最近使用项(shortcode, 常用Emoji短码.value, 常用Emoji最大数量)
  写入本地字符串列表(常用Emoji存储键, 常用Emoji短码.value)
}

function 记录常用颜文字(value: string) {
  if (!颜文字快捷值集合.has(value)) {
    return
  }

  常用颜文字.value = 更新最近使用项(value, 常用颜文字.value, 常用颜文字最大数量)
  写入本地字符串列表(常用颜文字存储键, 常用颜文字.value)
}

onMounted(async () => {
  初始化常用表情记录()
  document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  await nextTick()
  初始化工具栏折叠监听()
  调度工具栏折叠更新()
  await createEditor()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
  清理工具栏折叠监听()
  releaseImageCropPreviewUrl()
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
    restoreScrollAfterModeSwitch()
    updateCursorStatus()
    聚焦源码输入框且保留滚动()
    emit('modeChange', sourceMode)
    return
  }

  setMarkdown(sourceContent.value)
  await nextTick()
  restoreScrollAfterModeSwitch()
  updateCursorStatus()
  聚焦可视编辑器且保留滚动()
  emit('modeChange', sourceMode)
})

watch(
  () => [
    props.showScrollSync,
    props.formatContent,
    props.showPreviewToggle,
    props.previewEnabled,
    props.previewLayoutMode,
    props.previewType,
    props.showOutlineToggle,
    props.outlineVisible,
  ] as const,
  () => 调度工具栏折叠更新(),
)

function isTaskListCheckboxClick(view: EditorView, nodePos: number, event: MouseEvent): boolean {
  const nodeDom = view.nodeDOM(nodePos)
  if (!(nodeDom instanceof HTMLElement)) {
    return false
  }

  const rect = nodeDom.getBoundingClientRect()
  const style = window.getComputedStyle(nodeDom)
  const fontSize = Number.parseFloat(style.fontSize) || 16
  const lineHeight = Number.parseFloat(style.lineHeight) || fontSize * 1.5
  const checkboxLeft = rect.left - fontSize * 1.55
  const checkboxRight = rect.left - fontSize * 0.15
  const checkboxTop = rect.top
  const checkboxBottom = rect.top + Math.max(lineHeight, fontSize * 1.35)

  return (
    event.clientX >= checkboxLeft
    && event.clientX <= checkboxRight
    && event.clientY >= checkboxTop
    && event.clientY <= checkboxBottom
  )
}

function handleReverseInlineMarkdownInput(view: EditorView, from: number, to: number, text: string): boolean {
  if ((text !== '*' && text !== '`') || from !== to || view.composing) {
    return false
  }

  const match = findReverseInlineMarkdownMatch(view, from, text)
  if (!match) {
    return false
  }

  const tr = view.state.tr.insertText(text, from, to)
  tr.addMark(match.contentStart, match.contentEnd, match.markType.create(match.attrs))
  tr.delete(match.closingStart, match.closingEnd)
  tr.delete(match.openingStart, match.openingEnd)
  tr.setSelection(TextSelection.create(tr.doc, match.openingStart + match.contentEnd - match.contentStart))
  tr.removeStoredMark(match.markType)
  view.dispatch(tr.scrollIntoView())
  return true
}

function findReverseInlineMarkdownMatch(
  view: EditorView,
  from: number,
  text: string,
): ReverseInlineMarkdownMatch | null {
  const { state } = view
  const $from = state.doc.resolve(from)
  const parent = $from.parent
  if (!parent.isTextblock || parent.type.name !== 'paragraph') {
    return null
  }

  const paragraphStart = $from.start()
  const offset = from - paragraphStart
  const nextText = `${parent.textContent.slice(0, offset)}${text}${parent.textContent.slice(offset)}`
  const rules = 反向行内Markdown规则.filter((rule) => rule.delimiter.endsWith(text))

  for (const rule of rules) {
    const match = findReverseInlineMarkdownRuleMatch(
      state.schema.marks[rule.markName],
      rule,
      nextText,
      paragraphStart,
      offset,
    )
    if (match) {
      return match
    }
  }

  return null
}

function findReverseInlineMarkdownRuleMatch(
  markType: MarkType | undefined,
  rule: ReverseInlineMarkdownRule,
  text: string,
  paragraphStart: number,
  inputOffset: number,
): ReverseInlineMarkdownMatch | null {
  if (!markType) {
    return null
  }

  const delimiter = rule.delimiter
  const delimiterLength = delimiter.length
  const openingStartOffset = inputOffset - delimiterLength + 1
  const openingEndOffset = openingStartOffset + delimiterLength
  if (openingStartOffset < 0 || text.slice(openingStartOffset, openingEndOffset) !== delimiter) {
    return null
  }

  const closingStartOffset = text.indexOf(delimiter, openingEndOffset)
  if (closingStartOffset === -1) {
    return null
  }

  const content = text.slice(openingEndOffset, closingStartOffset)
  if (!isValidReverseInlineMarkdownContent(content, delimiter)) {
    return null
  }

  const closingEndOffset = closingStartOffset + delimiterLength
  if (!canApplyReverseInlineMarkdown(text, openingStartOffset, closingEndOffset, delimiter)) {
    return null
  }

  return {
    contentStart: paragraphStart + openingEndOffset,
    contentEnd: paragraphStart + closingStartOffset,
    openingStart: paragraphStart + openingStartOffset,
    openingEnd: paragraphStart + openingEndOffset,
    closingStart: paragraphStart + closingStartOffset,
    closingEnd: paragraphStart + closingEndOffset,
    markType,
    attrs: rule.attrs,
  }
}

function isValidReverseInlineMarkdownContent(content: string, delimiter: string): boolean {
  if (content.length === 0 || /^\s|\s$/.test(content) || content.includes('\n')) {
    return false
  }

  if (delimiter === '`') {
    return !content.includes('`')
  }

  return !content.includes('*')
}

function canApplyReverseInlineMarkdown(
  text: string,
  openingStartOffset: number,
  closingEndOffset: number,
  delimiter: string,
): boolean {
  if (delimiter === '*') {
    const closingStartOffset = closingEndOffset - delimiter.length
    return text[openingStartOffset + 1] !== '*' && text[closingStartOffset + 1] !== '*'
  }

  if (delimiter !== '**') {
    return true
  }

  const before = text[openingStartOffset - 1] ?? ''
  const after = text[closingEndOffset] ?? ''
  return !/[\w:/]/.test(before) && !/[\w/]/.test(after)
}

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
      configureMarkdownSerializer(ctx)
      ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
        if (isApplyingExternalMarkdown.value || !isEditorReadyForLocalUpdates.value) {
          return
        }

        const normalizedMarkdown = normalizeSerializedMarkdown(markdown)
        lastMarkdown.value = normalizedMarkdown
        emit('update:modelValue', normalizedMarkdown)
      })
    })
    .use(commonmarkEditorPlugins)
    .use(gfm)
    .use(highlightMarkdownPlugins)
    .use(markdownLinkInputRule)
    .use(reverseInlineMarkdownInput)
    .use(taskListCheckboxClickPlugin)
    .use(extendedMarkdownPreviewDecoration)
    .use(editorStatusPlugin)
    .use(history)
    .use(listener)
    .use(clipboard)
    .use(cursor)
    .use(indent)
    .use(trailing)

  try {
    editor.value = await milkdownEditor.create()
    lastMarkdown.value = props.modelValue
    isEditorReadyForLocalUpdates.value = true
    updateCursorStatus()
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
    return normalizeSerializedMarkdown(serializer(view.state.doc))
  })
}

function setMarkdown(markdown: string) {
  lastMarkdown.value = markdown

  if (isSourceMode.value) {
    sourceContent.value = markdown
    return
  }

  replaceEditorMarkdown(markdown)
}

function replaceEditorMarkdown(markdown: string): boolean {
  const currentEditor = editor.value
  if (!currentEditor) {
    return false
  }

  isApplyingExternalMarkdown.value = true
  try {
    currentEditor.action(replaceAll(markdown, true))
    return true
  } finally {
    isApplyingExternalMarkdown.value = false
  }
}

function formatMarkdown(): string | null {
  const sourceMarkdown = isSourceMode.value ? sourceContent.value : getMarkdown()
  if (!replaceEditorMarkdown(sourceMarkdown)) {
    return null
  }

  const formattedMarkdown = getMarkdown()
  lastMarkdown.value = formattedMarkdown
  if (isSourceMode.value) {
    sourceContent.value = formattedMarkdown
  }
  emit('update:modelValue', formattedMarkdown)
  return formattedMarkdown
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

function getScrollElement(): HTMLElement | null {
  if (isSourceMode.value) {
    return sourceTextareaRef.value
  }

  return getEditorView()?.dom ?? null
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

function scrollToHeading(headingIndex: number, sourceLine: number): boolean {
  if (headingIndex < 0) {
    return false
  }

  if (isSourceMode.value) {
    return scrollSourceToLine(sourceLine)
  }

  const view = getEditorView()
  if (!view) {
    return false
  }

  let currentHeadingIndex = -1
  let targetPosition: number | null = null
  view.state.doc.descendants((node, pos) => {
    if (node.type.name !== 'heading') {
      return true
    }

    currentHeadingIndex += 1
    if (currentHeadingIndex === headingIndex) {
      targetPosition = pos
      return false
    }

    return true
  })

  if (targetPosition === null) {
    return false
  }

  const selectionPosition = Math.min(targetPosition + 1, view.state.doc.content.size)
  const tr = view.state.tr.setSelection(
    TextSelection.near(view.state.doc.resolve(selectionPosition), 1),
  ).scrollIntoView()
  view.dispatch(tr)
  view.focus()
  return true
}

function scrollSourceToLine(sourceLine: number): boolean {
  const textarea = sourceTextareaRef.value
  if (!textarea || sourceLine <= 0) {
    return false
  }

  const lineStartOffset = getSourceLineStartOffset(sourceContent.value, sourceLine)
  textarea.focus()
  textarea.setSelectionRange(lineStartOffset, lineStartOffset)
  updateCursorStatus()

  const computedStyle = window.getComputedStyle(textarea)
  const parsedLineHeight = Number.parseFloat(computedStyle.lineHeight)
  const parsedFontSize = Number.parseFloat(computedStyle.fontSize)
  const lineHeight = Number.isFinite(parsedLineHeight)
    ? parsedLineHeight
    : (Number.isFinite(parsedFontSize) ? parsedFontSize * 1.75 : 24)
  const targetTop = Math.max(0, (sourceLine - 1) * lineHeight - textarea.clientHeight * 0.22)
  textarea.scrollTo({ top: targetTop, behavior: 'smooth' })
  return true
}

function getSourceLineStartOffset(source: string, sourceLine: number): number {
  if (sourceLine <= 1) {
    return 0
  }

  let currentLine = 1
  for (let index = 0; index < source.length; index += 1) {
    if (source[index] !== '\n') {
      continue
    }

    currentLine += 1
    if (currentLine === sourceLine) {
      return index + 1
    }
  }

  return source.length
}

function redoEdit(): boolean {
  const view = getEditorView()
  if (!view) {
    return false
  }

  return redo(view.state, view.dispatch)
}

function undoEdit(): boolean {
  const view = getEditorView()
  if (!view) {
    return false
  }

  return undo(view.state, view.dispatch)
}

function toggleHighlight() {
  const view = getEditorView()
  if (!view) {
    insertMarkdown(buildToolbarMarkdownSnippet('highlight'))
    return
  }

  const markType = view.state.schema.marks.highlight
  if (!markType) {
    insertMarkdown(buildToolbarMarkdownSnippet('highlight'))
    return
  }

  const { from, to, empty } = view.state.selection
  if (empty) {
    insertMarkdown(buildToolbarMarkdownSnippet('highlight'))
    return
  }

  const hasHighlight = view.state.doc.rangeHasMark(from, to, markType)
  const tr = hasHighlight
    ? view.state.tr.removeMark(from, to, markType)
    : view.state.tr.addMark(from, to, markType.create())
  view.dispatch(tr.scrollIntoView())
  lastMarkdown.value = getMarkdown()
  emit('update:modelValue', lastMarkdown.value)
}

function focus() {
  if (isSourceMode.value) {
    聚焦源码输入框且保留滚动()
    return
  }

  聚焦可视编辑器且保留滚动()
}

function 聚焦源码输入框且保留滚动() {
  sourceTextareaRef.value?.focus({ preventScroll: true })
}

function 聚焦可视编辑器且保留滚动() {
  getEditorView()?.dom.focus({ preventScroll: true })
}

function handleSourceInput() {
  lastMarkdown.value = sourceContent.value
  updateCursorStatus()
  emit('update:modelValue', sourceContent.value)
}

function handleSourceKeydown(event: KeyboardEvent) {
  if (isMarkdownStrongShortcut(event)) {
    event.preventDefault()
    toggleSourceStrong()
  }
}

function toggleSourceStrong() {
  const textarea = sourceTextareaRef.value
  if (!textarea) {
    insertMarkdown(buildToolbarMarkdownSnippet('strong'))
    return
  }

  const selectionStart = Math.min(textarea.selectionStart, textarea.selectionEnd)
  const selectionEnd = Math.max(textarea.selectionStart, textarea.selectionEnd)
  const selectedText = sourceContent.value.slice(selectionStart, selectionEnd)
  const nextText = selectedText || '加粗文本'
  sourceContent.value = [
    sourceContent.value.slice(0, selectionStart),
    `**${nextText}**`,
    sourceContent.value.slice(selectionEnd),
  ].join('')
  handleSourceInput()

  void nextTick(() => {
    textarea.focus({ preventScroll: true })
    const contentStart = selectionStart + 2
    const contentEnd = contentStart + nextText.length
    textarea.setSelectionRange(contentStart, contentEnd)
    updateCursorStatus()
  })
}

function updateSourceSelectionStatus() {
  updateCursorStatus()
}

function restoreScrollAfterModeSwitch() {
  if (pendingScrollRatioAfterModeSwitch === null) {
    return
  }

  const scrollRatio = pendingScrollRatioAfterModeSwitch
  pendingScrollRatioAfterModeSwitch = null
  window.requestAnimationFrame(() => {
    setScrollRatio(scrollRatio)
  })
}

function updateCursorStatus() {
  if (isSourceMode.value) {
    const textarea = sourceTextareaRef.value
    const selectionStart = textarea?.selectionStart ?? 0
    const selectionEnd = textarea?.selectionEnd ?? selectionStart
    cursorStatus.value = buildCursorStatusFromOffsets(sourceContent.value, selectionStart, selectionEnd)
    return
  }

  const view = getEditorView()
  if (!view) {
    cursorStatus.value = buildCursorStatusFromOffsets(lastMarkdown.value, 0, 0)
    return
  }

  const { state } = view
  const beforeCursor = state.doc.textBetween(0, state.selection.from, '\n', '\n')
  const selectedText = state.doc.textBetween(state.selection.from, state.selection.to, '\n', '\n')
  cursorStatus.value = buildCursorStatusFromText(beforeCursor, selectedText)
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

function buildCursorStatusFromText(beforeCursor: string, selectedText: string) {
  const normalizedBeforeCursor = beforeCursor.replace(/\r\n/g, '\n')
  return {
    line: normalizedBeforeCursor.length === 0 ? 1 : normalizedBeforeCursor.split('\n').length,
    selectedWords: countReadableWords(selectedText),
    selectedCharacters: Array.from(selectedText).length,
  }
}

function countReadableWords(text: string): number {
  const chineseCharacterCount = text.match(/[\u4e00-\u9fff]/g)?.length ?? 0
  const latinWordCount = text.match(/[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*/g)?.length ?? 0
  return chineseCharacterCount + latinWordCount
}

function getToolbarItemKey(item: ToolbarItem, index: number): string {
  return `${item.type ?? 'button'}-${item.action ?? index}`
}

function toggleSourceMode() {
  pendingScrollRatioAfterModeSwitch = getScrollRatio()
  isSourceMode.value = !isSourceMode.value
}

function runToolbarAction(action: ToolbarAction, payload?: string | number) {
  if (action === 'image') {
    openImagePicker()
    return
  }

  if (action === 'imageLink') {
    insertImageLink()
    return
  }

  if (action === 'imageCropUpload') {
    openCropImagePicker()
    return
  }

  if (action === 'sourceMode') {
    toggleSourceMode()
    return
  }

  if (action === 'undo') {
    undoEdit()
    focus()
    return
  }

  if (action === 'redo') {
    redoEdit()
    focus()
    return
  }

  if (action === 'format') {
    void props.formatContent?.()
    return
  }

  if (action === 'scrollSync') {
    if (props.previewLayoutMode !== 'split' || props.previewType === 'mindmap') {
      return
    }
    emit('update:scrollSync', !props.scrollSync)
    return
  }

  if (action === 'previewToggle') {
    emit('update:previewEnabled', !props.previewEnabled)
    return
  }

  if (action === 'previewLayoutToggle') {
    emit('update:previewLayoutMode', props.previewLayoutMode === 'split' ? 'full' : 'split')
    return
  }

  if (action === 'previewLayoutSplit') {
    emit('update:previewLayoutMode', 'split')
    return
  }

  if (action === 'previewLayoutFull') {
    emit('update:previewLayoutMode', 'full')
    return
  }

  if (action === 'previewTypeToggle') {
    if (props.previewType === 'preview') {
      emit('update:previewType', 'html')
      return
    }
    if (props.previewType === 'html') {
      emit('update:previewType', 'mindmap')
      return
    }
    emit('update:previewType', 'preview')
    return
  }

  if (action === 'previewTypePreview') {
    emit('update:previewType', 'preview')
    return
  }

  if (action === 'previewTypeHtml') {
    emit('update:previewType', 'html')
    return
  }

  if (action === 'previewTypeMindmap') {
    emit('update:previewType', 'mindmap')
    return
  }

  if (action === 'outlineToggle') {
    emit('update:outlineVisible', !props.outlineVisible)
    return
  }

  if (action === 'pageFullscreen') {
    togglePageFullscreen()
    return
  }

  if (action === 'fullscreen') {
    void toggleScreenFullscreen()
    return
  }

  if (action === 'customMarkdown') {
    const handled = runCustomMarkdownAction(payload)
    if (handled) {
      focus()
    }
    return
  }

  if (action === 'highlight' && !isSourceMode.value) {
    toggleHighlight()
    focus()
    return
  }

  if (shouldInsertMarkdownSnippet(action)) {
    insertMarkdown(buildToolbarMarkdownSnippet(action, payload))
    focus()
    return
  }

  if (isSourceMode.value) {
    runSourceModeAction(action, payload)
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
        return commands.call(wrapInHeadingCommand.key, normalizeHeadingLevel(payload))
      case 'strong':
        return commands.call(toggleStrongCommand.key)
      case 'emphasis':
        return commands.call(toggleEmphasisCommand.key)
      case 'strikethrough':
        return commands.call(toggleStrikethroughCommand.key)
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
      case 'taskList':
        return false
      case 'codeBlock':
        return commands.call(createCodeBlockCommand.key)
      case 'table':
        return commands.call(insertTableCommand.key, normalizeTableSizePayload(payload))
      case 'hr':
        return commands.call(insertHrCommand.key)
    }
  })

  if (!commandResult) {
    runSourceModeAction(action, payload)
  }

  lastMarkdown.value = getMarkdown()
  emit('update:modelValue', lastMarkdown.value)
  focus()
}

function runSourceModeAction(action: ToolbarAction, payload?: string | number) {
  switch (action) {
    case 'heading':
      insertMarkdown(`${'\n'}${'#'.repeat(normalizeHeadingLevel(payload))} 标题\n`)
      return
    case 'underline':
    case 'subscript':
    case 'superscript':
    case 'emphasis':
    case 'strikethrough':
    case 'highlight':
    case 'inlineCode':
    case 'link':
    case 'footnote':
    case 'abbr':
    case 'emojiShortcode':
    case 'mermaid':
    case 'math':
      insertMarkdown(buildToolbarMarkdownSnippet(action, payload))
      return
    case 'strong':
      toggleSourceStrong()
      return
    case 'customMarkdown':
      runCustomMarkdownAction(payload)
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
    case 'taskList':
      insertMarkdown('\n- [ ] 待办项\n')
      return
    case 'codeBlock':
      insertMarkdown('\n```ts\n\n```\n')
      return
    case 'table':
      insertMarkdown(buildTableMarkdown(normalizeTableSizePayload(payload)))
      return
    case 'hr':
      insertMarkdown('\n---\n')
      return
    case 'undo':
    case 'redo':
    case 'image':
    case 'imageLink':
    case 'imageCropUpload':
    case 'format':
    case 'scrollSync':
    case 'previewToggle':
    case 'previewLayoutToggle':
    case 'previewLayoutSplit':
    case 'previewLayoutFull':
    case 'previewTypeToggle':
    case 'previewTypePreview':
    case 'previewTypeHtml':
    case 'previewTypeMindmap':
    case 'outlineToggle':
    case 'pageFullscreen':
    case 'fullscreen':
    case 'sourceMode':
      return
  }
}

function normalizeHeadingLevel(payload?: string | number): 1 | 2 | 3 | 4 | 5 | 6 {
  const level = Number(payload ?? 1)
  if (level >= 1 && level <= 6) {
    return level as 1 | 2 | 3 | 4 | 5 | 6
  }

  return 1
}

function normalizeTableSizePayload(payload?: string | number): { row: number; col: number } {
  if (typeof payload === 'string') {
    const [row, col] = payload.split('x').map((item) => Number(item))
    return {
      row: normalizeTableSize(row, 3),
      col: normalizeTableSize(col, 3),
    }
  }

  return { row: 3, col: 3 }
}

function normalizeTableSize(value: number, fallback: number): number {
  if (!Number.isInteger(value)) {
    return fallback
  }

  return Math.min(6, Math.max(1, value))
}

function normalizeCustomTableSize(value: number, fallback: number): number {
  if (!Number.isInteger(value)) {
    return fallback
  }

  return Math.min(更多表格最大行列, Math.max(1, value))
}

function buildTableMarkdown(size: { row: number; col: number }): string {
  const header = `| ${Array.from({ length: size.col }, (_, index) => `列 ${index + 1}`).join(' | ')} |`
  const separator = `| ${Array.from({ length: size.col }, () => '---').join(' | ')} |`
  const bodyRows = Array.from(
    { length: Math.max(1, size.row - 1) },
    () => `| ${Array.from({ length: size.col }, () => '').join(' | ')} |`,
  )
  return `\n${[header, separator, ...bodyRows].join('\n')}\n`
}

function shouldInsertMarkdownSnippet(action: ToolbarAction): boolean {
  return [
    'underline',
    'subscript',
    'superscript',
    'footnote',
    'abbr',
    'emojiShortcode',
    'mermaid',
    'math',
  ].includes(action)
}

function buildToolbarMarkdownSnippet(action: ToolbarAction, payload?: string | number): string {
  switch (action) {
    case 'underline':
      return '<u>下划线文本</u>'
    case 'subscript':
      return '<sub>下标</sub>'
    case 'superscript':
      return '<sup>上标</sup>'
    case 'strong':
      return '**加粗文本**'
    case 'emphasis':
      return '*斜体文本*'
    case 'strikethrough':
      return '~~删除线文本~~'
    case 'highlight':
      return '==高亮文本=='
    case 'inlineCode':
      return '`代码`'
    case 'link':
      return '[链接文本](https://example.com)'
    case 'footnote':
      return '\n这里需要脚注[^1]\n\n[^1]: 脚注内容\n'
    case 'abbr':
      return '\nHTML 是常见缩写。\n\n*[HTML]: HyperText Markup Language\n'
    case 'emojiShortcode':
      return ':smile:'
    case 'mermaid':
      return buildMermaidSnippet(String(payload ?? 'flow'))
    case 'math':
      return payload === 'block' ? '\n$$\nE = mc^2\n$$\n' : '$E = mc^2$'
    default:
      return ''
  }
}

function runCustomMarkdownAction(payload?: string | number): boolean {
  const snippetType = normalizeCustomMarkdownSnippet(payload)
  if (!snippetType) {
    return false
  }

  if (snippetType === 'github-card') {
    openGithubCardDialog()
    return true
  }

  if (snippetType === 'github-alert-syntax' || snippetType === 'code-syntax') {
    openCustomMarkdownSyntaxDialog(snippetType)
    return true
  }

  insertMarkdown(buildCustomMarkdownSnippet(snippetType))
  return true
}

function openCustomMarkdownSyntaxDialog(type: 'github-alert-syntax' | 'code-syntax') {
  syntaxDialogTitle.value = type === 'github-alert-syntax' ? 'GitHub 风格提示块语法' : '增强代码块语法'
  syntaxDialogContent.value = type === 'github-alert-syntax'
    ? buildGithubAlertSyntaxSnippet()
    : buildCodeSyntaxSnippet()
  syntaxDialogVisible.value = true
}

function closeSyntaxDialog() {
  syntaxDialogVisible.value = false
}

function insertEmojiShortcode(shortcode: string) {
  记录常用Emoji(shortcode)
  insertMarkdown(`:${shortcode}:`)
  closeEmojiDialog()
  closeToolbarDropdown()
  focus()
}

function insertKaomoji(value: string) {
  记录常用颜文字(value)
  insertMarkdown(value)
  closeToolbarDropdown()
  focus()
}

function openEmojiDialog() {
  emojiDialogVisible.value = true
  closeToolbarDropdown()
}

function closeEmojiDialog() {
  emojiDialogVisible.value = false
}

function openTableDialog() {
  tableDialogRows.value = Math.max(8, hoveredTableRows.value)
  tableDialogCols.value = Math.max(8, hoveredTableCols.value)
  tableDialogVisible.value = true
  closeToolbarDropdown()
  void nextTick(() => {
    tableDialogRowsInputRef.value?.focus()
  })
}

function closeTableDialog() {
  tableDialogVisible.value = false
}

function confirmTableDialogInsert() {
  const row = normalizeCustomTableSize(tableDialogRows.value, 8)
  const col = normalizeCustomTableSize(tableDialogCols.value, 8)
  tableDialogRows.value = row
  tableDialogCols.value = col
  insertMarkdown(buildTableMarkdown({ row, col }))
  closeTableDialog()
  focus()
}

function openGithubCardDialog() {
  githubCardRepoInput.value = ''
  githubCardRepoError.value = ''
  githubCardDialogVisible.value = true
  void nextTick(() => {
    githubCardRepoInputRef.value?.focus()
  })
}

function closeGithubCardDialog() {
  githubCardDialogVisible.value = false
}

function confirmGithubCardInsert() {
  const repo = githubCardRepoInput.value.trim()
  if (!repo) {
    githubCardRepoError.value = '请输入 GitHub 仓库，例如 owner/repo'
    return
  }

  if (!isValidGithubRepoName(repo)) {
    githubCardRepoError.value = 'GitHub 仓库格式应为 owner/repo，只能包含字母、数字、点、短横线和下划线'
    return
  }

  insertMarkdown(`\n::${GitHub卡片语法名称}{repo="${repo}"}\n`)
  closeGithubCardDialog()
}

function isValidGithubRepoName(repo: string): boolean {
  return /^[A-Za-z0-9][A-Za-z0-9-]{0,38}\/[A-Za-z0-9._-]+$/.test(repo)
}

function getFullscreenRoot(): HTMLElement | null {
  const root = rootRef.value?.closest('.milkdown-markdown-editor')
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

  root.classList.toggle('milkdown-markdown-editor--page-fullscreen')
  void nextTick(() => {
    root.scrollIntoView({ block: 'nearest' })
    window.dispatchEvent(new Event('resize'))
  })
}

async function toggleScreenFullscreen() {
  const root = getFullscreenRoot()
  if (!(root instanceof HTMLElement) || !document.fullscreenEnabled) {
    togglePageFullscreen()
    return
  }

  if (document.fullscreenElement) {
    await document.exitFullscreen()
    return
  }

  await root.requestFullscreen()
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

defineExpose<MilkdownMarkdown编辑器实例>({
  getMarkdown,
  setMarkdown,
  formatMarkdown,
  insertMarkdown,
  getEditorView,
  getScrollElement,
  getScrollRatio,
  setScrollRatio,
  scrollToHeading,
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
    <MilkdownMarkdown工具栏
      ref="toolbarRef"
      v-model:hovered-table-rows="hoveredTableRows"
      v-model:hovered-table-cols="hoveredTableCols"
      v-model:emoji-picker-mode="emojiPickerMode"
      :dark="props.theme === 'dark'"
      :items="toolbarItems"
      :overflow-items="溢出工具栏菜单项"
      :active-dropdown-key="activeDropdownKey"
      :active-dropdown-style="activeDropdownStyle"
      :active-overflow-submenu-key="activeOverflowSubmenuKey"
      :toolbar-overflow-count="toolbarOverflowCount"
      :formula-index="工具栏公式索引"
      :more-key="工具栏更多键"
      :table-size-options="表格行列选项"
      :common-emoji-options="常用Emoji选项"
      :light-emoji-options="轻量Emoji选项"
      :common-kaomoji-options="常用颜文字选项"
      :kaomoji-options="颜文字选项"
      :get-item-key="getToolbarItemKey"
      :get-icon="getToolbarIcon"
      :get-title="getToolbarTitle"
      :should-show-item="shouldShowToolbarItem"
      :should-show-separator="shouldShowToolbarSeparator"
      @toggle-dropdown="toggleToolbarDropdown"
      @open-dropdown="openToolbarDropdown"
      @toggle-more-dropdown="toggleToolbarMoreDropdown"
      @open-more-dropdown="openToolbarMoreDropdown"
      @open-overflow-submenu="openToolbarOverflowSubmenu"
      @overflow-menu-click="handleToolbarOverflowMenuClick"
      @overflow-submenu-click="handleToolbarOverflowSubmenuClick"
      @run-action="runToolbarAction"
      @close-dropdown="closeToolbarDropdown"
      @open-table-dialog="openTableDialog"
      @insert-emoji-shortcode="insertEmojiShortcode"
      @insert-kaomoji="insertKaomoji"
      @open-emoji-dialog="openEmojiDialog"
    >
      <input
        ref="fileInputRef"
        class="milkdown-markdown-editor__file-input"
        type="file"
        accept="image/*"
        multiple
        @change="handleFileInputChange"
      >
      <input
        ref="cropFileInputRef"
        class="milkdown-markdown-editor__file-input"
        type="file"
        accept="image/*"
        @change="handleCropFileInputChange"
      >
    </MilkdownMarkdown工具栏>

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
        @keydown="handleSourceKeydown"
        @click="updateSourceSelectionStatus"
        @keyup="updateSourceSelectionStatus"
        @select="updateSourceSelectionStatus"
      />
      <div v-if="loading" class="milkdown-markdown-editor__loading">
        正在加载编辑器...
      </div>
    </div>

    <MilkdownMarkdown编辑器底部状态栏
      :mode-label="editorModeLabel"
      :uploading="isUploading"
      :cursor-status="cursorStatus"
      :stats="editorStats"
    />

    <MilkdownMarkdown图片裁剪弹窗
      v-model:rect="imageCropRect"
      :visible="imageCropDialogVisible"
      :preview-url="imageCropPreviewUrl"
      :natural-size="imageCropNaturalSize"
      :uploading="isUploading"
      @close="closeImageCropDialog"
      @reset="resetImageCropRect"
      @confirm="confirmImageCropUpload"
    />

    <div
      v-if="syntaxDialogVisible"
      class="milkdown-markdown-editor__syntax-dialog"
      role="dialog"
      aria-modal="true"
      :aria-label="syntaxDialogTitle"
      @click.self="closeSyntaxDialog"
    >
      <div class="milkdown-markdown-editor__syntax-panel">
        <div class="milkdown-markdown-editor__syntax-header">
          <strong>{{ syntaxDialogTitle }}</strong>
          <button
            class="milkdown-markdown-editor__syntax-close"
            type="button"
            title="关闭"
            @click="closeSyntaxDialog"
          >
            关闭
          </button>
        </div>
        <pre class="milkdown-markdown-editor__syntax-content"><code>{{ syntaxDialogContent }}</code></pre>
      </div>
    </div>

    <div
      v-if="tableDialogVisible"
      class="milkdown-markdown-editor__table-dialog"
      role="dialog"
      aria-modal="true"
      aria-label="插入更多表格"
      @click.self="closeTableDialog"
    >
      <form class="milkdown-markdown-editor__table-panel" @submit.prevent="confirmTableDialogInsert">
        <div class="milkdown-markdown-editor__table-header">
          <strong>插入更多表格</strong>
          <button
            class="milkdown-markdown-editor__table-close"
            type="button"
            title="关闭"
            @click="closeTableDialog"
          >
            关闭
          </button>
        </div>
        <div class="milkdown-markdown-editor__table-body">
          <div class="milkdown-markdown-editor__table-fields">
            <label class="milkdown-markdown-editor__table-field">
              <span>行数</span>
              <input
                ref="tableDialogRowsInputRef"
                v-model.number="tableDialogRows"
                class="milkdown-markdown-editor__table-input"
                type="number"
                min="1"
                :max="更多表格最大行列"
                step="1"
              >
            </label>
            <label class="milkdown-markdown-editor__table-field">
              <span>列数</span>
              <input
                v-model.number="tableDialogCols"
                class="milkdown-markdown-editor__table-input"
                type="number"
                min="1"
                :max="更多表格最大行列"
                step="1"
              >
            </label>
          </div>
          <div class="milkdown-markdown-editor__table-preview">
            <span class="milkdown-markdown-editor__table-preview-title">表格语法</span>
            <pre class="milkdown-markdown-editor__table-preview-content"><code>{{ 表格基础语法说明 }}</code></pre>
          </div>
        </div>
        <div class="milkdown-markdown-editor__table-footer">
          <span>最大支持 {{ 更多表格最大行列 }} x {{ 更多表格最大行列 }}</span>
          <div class="milkdown-markdown-editor__table-actions">
            <button type="button" @click="closeTableDialog">取消</button>
            <button type="submit" class="is-primary">插入</button>
          </div>
        </div>
      </form>
    </div>

    <div
      v-if="emojiDialogVisible"
      class="milkdown-markdown-editor__emoji-dialog"
      role="dialog"
      aria-modal="true"
      aria-label="选择全部 Emoji"
      @click.self="closeEmojiDialog"
    >
      <div class="milkdown-markdown-editor__emoji-panel">
        <div class="milkdown-markdown-editor__emoji-header">
          <strong>选择全部 Emoji</strong>
          <button
            class="milkdown-markdown-editor__emoji-close"
            type="button"
            title="关闭"
            @click="closeEmojiDialog"
          >
            关闭
          </button>
        </div>
        <div class="milkdown-markdown-editor__emoji-dialog-grid">
          <button
            v-for="option in 全量Emoji选项"
            :key="`full-${option.shortcode}`"
            class="milkdown-markdown-editor__emoji-dialog-item"
            type="button"
            :title="`:${option.shortcode}:`"
            @click="insertEmojiShortcode(option.shortcode)"
          >
            <span class="milkdown-markdown-editor__emoji-symbol">{{ option.emoji }}</span>
            <span class="milkdown-markdown-editor__emoji-shortcode">:{{ option.shortcode }}:</span>
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="githubCardDialogVisible"
      class="milkdown-markdown-editor__github-card-dialog"
      role="dialog"
      aria-modal="true"
      aria-label="插入 GitHub 仓库卡片"
      @click.self="closeGithubCardDialog"
    >
      <form class="milkdown-markdown-editor__github-card-panel" @submit.prevent="confirmGithubCardInsert">
        <div class="milkdown-markdown-editor__github-card-header">
          <strong>插入 GitHub 仓库卡片</strong>
          <button
            class="milkdown-markdown-editor__github-card-close"
            type="button"
            title="关闭"
            @click="closeGithubCardDialog"
          >
            关闭
          </button>
        </div>
        <div class="milkdown-markdown-editor__github-card-body">
          <label class="milkdown-markdown-editor__github-card-field">
            <span>仓库</span>
            <input
              ref="githubCardRepoInputRef"
              v-model="githubCardRepoInput"
              class="milkdown-markdown-editor__github-card-input"
              type="text"
              placeholder="owner/repo"
              autocomplete="off"
              @input="githubCardRepoError = ''"
            >
          </label>
          <p
            v-if="githubCardRepoError"
            class="milkdown-markdown-editor__github-card-error"
          >
            {{ githubCardRepoError }}
          </p>
        </div>
        <div class="milkdown-markdown-editor__github-card-footer">
          <button type="button" @click="closeGithubCardDialog">取消</button>
          <button type="submit" class="is-primary">插入</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped src="../styles/milkdown-markdown-editor-content.css"></style>

<style scoped>
.milkdown-markdown-editor {
  --milkdown-markdown-toolbar-height: 37px;
  --milkdown-markdown-primary: var(--primary, var(--el-color-primary));
  --milkdown-markdown-text-primary: var(--text-primary, var(--el-text-color-primary));
  --milkdown-markdown-text-secondary: var(--text-secondary, var(--el-text-color-secondary));
  --milkdown-markdown-text-tertiary: var(--text-tertiary, var(--el-text-color-placeholder));
  --milkdown-markdown-card-bg: var(--bg-card, var(--el-bg-color-overlay));
  --milkdown-markdown-soft-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 72%,
    var(--milkdown-markdown-card-bg)
  );
  --milkdown-markdown-hover-bg: var(--bg-hover, color-mix(in srgb, var(--el-color-primary) 8%, transparent));
  --milkdown-markdown-border: var(--border-color, var(--el-border-color));
  --milkdown-markdown-inline-code-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 72%,
    transparent
  );
  --milkdown-markdown-inline-code-text: color-mix(
    in srgb,
    var(--milkdown-markdown-text-secondary) 76%,
    var(--milkdown-markdown-text-primary)
  );
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 720px;
  min-height: 360px;
  overflow: hidden;
  border-radius: 12px;
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
  color: var(--milkdown-markdown-text-primary);
}

.milkdown-markdown-editor__file-input {
  display: none;
}

.milkdown-markdown-editor__content {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  background: var(--milkdown-markdown-editor-content-bg, transparent);
  background-color: var(--milkdown-markdown-editor-content-bg-color, transparent);
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
  min-height: 100%;
  padding: 20px 24px;
  resize: none;
  outline: none;
  background: transparent;
  color: var(--milkdown-markdown-text-primary);
  caret-color: var(--milkdown-markdown-text-primary);
  font: 14px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor__source::placeholder {
  color: var(--milkdown-markdown-text-tertiary);
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
  background: color-mix(
    in srgb,
    var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay)) 86%,
    transparent
  );
  backdrop-filter: blur(3px);
}

.milkdown-markdown-editor__syntax-dialog {
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

.milkdown-markdown-editor__syntax-panel {
  display: flex;
  flex-direction: column;
  width: min(720px, 100%);
  max-height: min(680px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-editor__syntax-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-editor__syntax-close {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__syntax-content {
  margin: 0;
  padding: 16px;
  overflow: auto;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--el-bg-color));
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.milkdown-markdown-editor__table-dialog {
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

.milkdown-markdown-editor__table-panel {
  display: flex;
  flex-direction: column;
  width: min(620px, 100%);
  max-height: min(680px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-editor__table-header,
.milkdown-markdown-editor__table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-editor__table-footer {
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.milkdown-markdown-editor__table-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 14px;
  box-sizing: border-box;
  overflow: auto;
}

.milkdown-markdown-editor__table-fields,
.milkdown-markdown-editor__table-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.milkdown-markdown-editor__table-field {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-editor__table-input {
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  outline: none;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font: inherit;
}

.milkdown-markdown-editor__table-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.milkdown-markdown-editor__table-preview {
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 8px;
}

.milkdown-markdown-editor__table-preview-title {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-editor__table-preview-content {
  max-height: 300px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 6px;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--el-bg-color));
  color: var(--el-text-color-primary);
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor__table-close,
.milkdown-markdown-editor__table-actions button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__table-actions button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}

.milkdown-markdown-editor__emoji-dialog {
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

.milkdown-markdown-editor__emoji-panel {
  display: flex;
  flex-direction: column;
  width: min(760px, 100%);
  max-height: min(680px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-editor__emoji-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-editor__emoji-close {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__emoji-dialog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(108px, 1fr));
  gap: 6px;
  padding: 12px;
  overflow: auto;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__emoji-dialog-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  min-height: 34px;
  padding: 0 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__emoji-dialog-item:hover,
.milkdown-markdown-editor__emoji-dialog-item:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__emoji-shortcode {
  min-width: 0;
  overflow: hidden;
  font: 12px/1.2 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.milkdown-markdown-editor__github-card-dialog {
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

.milkdown-markdown-editor__github-card-panel {
  display: flex;
  flex-direction: column;
  width: min(420px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-editor__github-card-header,
.milkdown-markdown-editor__github-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-editor__github-card-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
}

.milkdown-markdown-editor__github-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 14px;
  box-sizing: border-box;
}

.milkdown-markdown-editor__github-card-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-editor__github-card-input {
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  outline: none;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font: inherit;
}

.milkdown-markdown-editor__github-card-input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.milkdown-markdown-editor__github-card-error {
  margin: 0;
  color: var(--el-color-danger);
  font-size: 12px;
  line-height: 1.5;
}

.milkdown-markdown-editor__github-card-close,
.milkdown-markdown-editor__github-card-footer button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__github-card-footer button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}

.milkdown-markdown-editor--dark {
  --milkdown-markdown-text-primary: var(--text-primary, #f3f4f6);
  --milkdown-markdown-text-secondary: var(--text-secondary, #d1d5db);
  --milkdown-markdown-text-tertiary: var(--text-tertiary, #9ca3af);
  --milkdown-markdown-card-bg: var(--bg-card, var(--el-bg-color-overlay));
  --milkdown-markdown-soft-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 82%,
    var(--milkdown-markdown-card-bg)
  );
  --milkdown-markdown-inline-code-bg: color-mix(
    in srgb,
    var(--bg-secondary, var(--el-fill-color-light)) 80%,
    transparent
  );
  --milkdown-markdown-inline-code-text: color-mix(
    in srgb,
    var(--milkdown-markdown-text-secondary) 76%,
    var(--milkdown-markdown-text-primary)
  );
  --milkdown-markdown-border: var(--border-color, var(--el-border-color));
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
}

.milkdown-markdown-editor--page-fullscreen {
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
  .milkdown-markdown-editor {
    height: 560px;
  }

  .milkdown-markdown-editor__source {
    padding: 16px;
  }

}
</style>
