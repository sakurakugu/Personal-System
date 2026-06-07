<script setup lang="ts">
import {
  Bold,
  ChartArea,
  Code,
  Expand,
  Forward,
  Heading,
  Image,
  Italic,
  Link,
  List,
  ListOrdered,
  ListTodo,
  Maximize2,
  Quote,
  Reply,
  SquareCode,
  SquareSigma,
  Strikethrough,
  Subscript,
  Superscript,
  Table,
  Underline,
} from 'lucide-vue-next'
import type { Component } from 'vue'
import { commandsCtx, Editor, defaultValueCtx, editorViewCtx, parserCtx, rootCtx, serializerCtx } from '@milkdown/core'
import type { MilkdownPlugin } from '@milkdown/ctx'
import { history } from '@milkdown/plugin-history'
import { listener, listenerCtx } from '@milkdown/plugin-listener'
import { clipboard } from '@milkdown/plugin-clipboard'
import { cursor } from '@milkdown/plugin-cursor'
import { indent } from '@milkdown/plugin-indent'
import { trailing } from '@milkdown/plugin-trailing'
import {
  commands as commonmarkCommands,
  createCodeBlockInputRule,
  createCodeBlockCommand,
  emphasisStarInputRule,
  emphasisUnderscoreInputRule,
  insertHrCommand,
  inlineCodeInputRule,
  keymap as commonmarkKeymap,
  linkSchema,
  listItemSchema,
  plugins as commonmarkPlugins,
  schema as commonmarkSchema,
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
import { gfm } from '@milkdown/preset-gfm'
import { insertTableCommand, toggleStrikethroughCommand } from '@milkdown/preset-gfm'
import { redo, undo } from '@milkdown/prose/history'
import { InputRule } from '@milkdown/prose/inputrules'
import type { MarkType, Node as ProseNode } from '@milkdown/prose/model'
import { liftListItem } from '@milkdown/prose/schema-list'
import { Plugin, TextSelection } from '@milkdown/prose/state'
import type { Parser } from '@milkdown/transformer'
import { $inputRule, $prose, insert, replaceAll } from '@milkdown/utils'
import { Decoration, DecorationSet, type EditorView } from '@milkdown/prose/view'
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
  getScrollElement: () => HTMLElement | null
  getScrollRatio: () => number
  setScrollRatio: (ratio: number) => void
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
}>(), {
  placeholder: '在此编写 Markdown 内容...',
  theme: 'light',
  uploadImages: undefined,
  formatContent: undefined,
  fullscreenRootSelector: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  ready: []
  loadingChange: [value: boolean]
  uploadError: [error: unknown]
  modeChange: [sourceMode: boolean]
}>()

const rootRef = ref<HTMLDivElement | null>(null)
const sourceTextareaRef = ref<HTMLTextAreaElement | null>(null)
const editor = ref<Editor | null>(null)
const activeDropdownKey = ref('')
const activeDropdownStyle = ref<Record<string, string>>({})
const hoveredTableRows = ref(3)
const hoveredTableCols = ref(3)
const loading = ref(true)
const isSourceMode = ref(false)
const sourceContent = ref('')
const lastMarkdown = ref(props.modelValue)
const isApplyingExternalMarkdown = ref(false)
const isEditorReadyForLocalUpdates = ref(false)
const isMilkdownContentPristine = ref(true)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
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
  $prose((ctx) => createMarkdownKeyboardPlugin(ctx.get(parserCtx), listItemSchema.type(ctx))),
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
const 表格简写正则 = /^\|(.+)\|\s*$/
const 代码围栏起始正则 = /^(`{3,}|~{3,})([a-zA-Z0-9_-]*)\s*$/
const 标签页标题转义正则 = /^\\(===\s+"(?:[^"\\]|\\.)+"\s*)$/gm
const 标签页压缩代码块正则 = /^\\===\s+"((?:[^"\\]|\\.)+)"\s*\n`([a-zA-Z0-9_-]+)\s+([^`\n]+)`/gm
const 缩写定义正则 = /^\\?\*\[([^\]\n]+)]:(\s+.+)$/gm
const GitHub提示块正则 = /^(?:>\s*)?\\?\[!([A-Za-z][\w-]*)](.*)$/gm
const 转义GitHub提示块正文正则 = /\\\[!([A-Za-z][\w-]*)]/g
const 转义缩写定义正则 = /^\\\*\[([^\]\n]+)]:(\s+.+)$/gm
const 转义Emoji短码正则 = /\\:([a-zA-Z0-9_+-]+)\\:/g
const 转义剧透文本正则 = /\\?:spoiler\\?\[((?:[^\]\\]|\\.)*)\\?]/g
const 转义GitHub卡片正则 = /\\?:\\?:github\\?\{repo=\\?"([^"\\]+\/[^"\\]+)\\?"\\?}/g
const 转义块级数学围栏正则 = /^\\\$\\\$\s*$/
const 转义块级数学围栏全局正则 = /^\\\$\\\$\s*$/gm
const 转义行内数学正则 = /(^|[^\\])\\\$([^$\n]+?)\\\$/g
const Emoji短码正则 = /:([a-zA-Z0-9_+-]+):/g
const 剧透文本正则 = /\\?:spoiler\\?\[((?:[^\]\\]|\\.)*)\\?]/g
const 行内数学正则 = /(^|[^\\])\$([^$\n]+?)\$/g
const GitHub卡片正则 = /\\?:\\?:github\\?\{repo=\\?"([^"\\]+\/[^"\\]+)\\?"\\?}/g
const GitHub提示块类型集合 = new Set([
  'NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION',
  'ABSTRACT', 'SUMMARY', 'TLDR', 'INFO', 'TODO',
  'SUCCESS', 'CHECK', 'DONE', 'QUESTION', 'HELP', 'FAQ',
  'ATTENTION', 'FAILURE', 'MISSING', 'FAIL', 'DANGER',
  'ERROR', 'BUG', 'EXAMPLE', 'QUOTE', 'CITE',
])

type MarkdownTextBlock = {
  node: ProseNode
  pos: number
  from: number
  to: number
  text: string
}

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

type ToolbarAction =
  | 'heading'
  | 'underline'
  | 'subscript'
  | 'superscript'
  | 'strong'
  | 'emphasis'
  | 'strikethrough'
  | 'link'
  | 'inlineCode'
  | 'blockquote'
  | 'bulletList'
  | 'orderedList'
  | 'taskList'
  | 'codeBlock'
  | 'table'
  | 'hr'
  | 'image'
  | 'mermaid'
  | 'math'
  | 'undo'
  | 'redo'
  | 'format'
  | 'pageFullscreen'
  | 'fullscreen'
  | 'sourceMode'

type ToolbarItemType = 'button' | 'dropdown' | 'separator' | 'spacer'

interface ToolbarDropdownOption {
  label: string
  title: string
  action: ToolbarAction
  payload?: string | number
}

interface ToolbarItem {
  type?: ToolbarItemType
  label: string
  title: string
  action?: ToolbarAction
  icon?: Component
  dropdown?: ToolbarDropdownOption[]
  hidden?: () => boolean
  disabled?: () => boolean
  active?: () => boolean
}

const 表格行列选项 = [1, 2, 3, 4, 5, 6]

const toolbarItems: ToolbarItem[] = [
  { label: '加粗', title: '加粗', action: 'strong', icon: Bold },
  { label: '下划线', title: '下划线', action: 'underline', icon: Underline },
  { label: '斜体', title: '斜体', action: 'emphasis', icon: Italic },
  { label: '删除线', title: '删除线', action: 'strikethrough', icon: Strikethrough },
  { type: 'separator', label: '', title: '' },
  {
    type: 'dropdown',
    label: '标题',
    title: '标题',
    action: 'heading',
    icon: Heading,
    dropdown: [
      { label: '一级标题', title: '一级标题', action: 'heading', payload: 1 },
      { label: '二级标题', title: '二级标题', action: 'heading', payload: 2 },
      { label: '三级标题', title: '三级标题', action: 'heading', payload: 3 },
      { label: '四级标题', title: '四级标题', action: 'heading', payload: 4 },
      { label: '五级标题', title: '五级标题', action: 'heading', payload: 5 },
      { label: '六级标题', title: '六级标题', action: 'heading', payload: 6 },
    ],
  },
  { label: '下标', title: '下标', action: 'subscript', icon: Subscript },
  { label: '上标', title: '上标', action: 'superscript', icon: Superscript },
  { label: '引用', title: '引用', action: 'blockquote', icon: Quote },
  { label: '无序列表', title: '无序列表', action: 'bulletList', icon: List },
  { label: '有序列表', title: '有序列表', action: 'orderedList', icon: ListOrdered },
  { label: '任务列表', title: '任务列表', action: 'taskList', icon: ListTodo },
  { type: 'separator', label: '', title: '' },
  { label: '行内代码', title: '行内代码', action: 'inlineCode', icon: Code },
  { label: '块级代码', title: '块级代码', action: 'codeBlock', icon: SquareCode },
  { label: '超链接', title: '超链接', action: 'link', icon: Link },
  { label: '图片', title: '图片', action: 'image', icon: Image, hidden: () => !props.uploadImages, disabled: () => isUploading.value },
  { type: 'dropdown', label: '表格', title: '表格', action: 'table', icon: Table },
  {
    type: 'dropdown',
    label: '各种图',
    title: '各种图',
    action: 'mermaid',
    icon: ChartArea,
    dropdown: [
      { label: '流程图', title: '流程图', action: 'mermaid', payload: 'flow' },
      { label: '时序图', title: '时序图', action: 'mermaid', payload: 'sequence' },
      { label: '甘特图', title: '甘特图', action: 'mermaid', payload: 'gantt' },
      { label: '类图', title: '类图', action: 'mermaid', payload: 'class' },
      { label: '状态图', title: '状态图', action: 'mermaid', payload: 'state' },
      { label: '饼图', title: '饼图', action: 'mermaid', payload: 'pie' },
      { label: '关系图', title: '关系图', action: 'mermaid', payload: 'relationship' },
      { label: '旅程图', title: '旅程图', action: 'mermaid', payload: 'journey' },
    ],
  },
  {
    type: 'dropdown',
    label: '公式',
    title: '公式',
    action: 'math',
    icon: SquareSigma,
    dropdown: [
      { label: '行内公式', title: '行内公式', action: 'math', payload: 'inline' },
      { label: '块级公式', title: '块级公式', action: 'math', payload: 'block' },
    ],
  },
  { type: 'separator', label: '', title: '' },
  { label: '后退', title: '后退', action: 'undo', icon: Reply },
  { label: '前进', title: '前进', action: 'redo', icon: Forward },
  { type: 'spacer', label: '', title: '' },
  { label: '美化', title: '美化', action: 'format', icon: SquareCode, hidden: () => !props.formatContent },
  {
    label: '源码',
    title: '源码和显示模式切换',
    action: 'sourceMode',
    icon: Code,
    active: () => isSourceMode.value,
  },
  { label: '浏览器全屏', title: '浏览器全屏', action: 'pageFullscreen', icon: Maximize2 },
  { label: '屏幕全屏', title: '屏幕全屏', action: 'fullscreen', icon: Expand },
]

const currentMarkdown = computed(() => (isSourceMode.value ? sourceContent.value : lastMarkdown.value))
const editorStats = computed(() => buildEditorStats(currentMarkdown.value))
const editorModeLabel = computed(() => (isSourceMode.value ? '源码' : '所见即所得'))
const rootClass = computed(() => ({
  'milkdown-markdown-editor--dark': props.theme === 'dark',
  'milkdown-markdown-editor--source': isSourceMode.value,
  'milkdown-markdown-editor--uploading': isUploading.value,
}))

onMounted(async () => {
  document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  await nextTick()
  await createEditor()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
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
    sourceTextareaRef.value?.focus()
    emit('modeChange', sourceMode)
    return
  }

  setMarkdown(sourceContent.value)
  await nextTick()
  restoreScrollAfterModeSwitch()
  updateCursorStatus()
  getEditorView()?.focus()
  emit('modeChange', sourceMode)
})

function createMarkdownKeyboardPlugin(parser: Parser, listItemType: ProseNode['type']) {
  return new Plugin({
    props: {
      handleKeyDown(view, event) {
        if (event.isComposing || event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) {
          return false
        }

        if (event.key === 'Enter') {
          return handleMarkdownEnter(view, parser)
        }

        if (event.key === 'Backspace') {
          return handleMarkdownBackspace(view, listItemType)
        }

        return false
      },
    },
  })
}

function handleMarkdownEnter(view: EditorView, parser: Parser): boolean {
  const { state } = view
  const { selection } = state
  if (!selection.empty) {
    return false
  }

  const $from = selection.$from
  const parent = $from.parent
  if (!parent.isTextblock || parent.type.name !== 'paragraph') {
    return false
  }

  const paragraphStart = $from.start()
  const paragraphEnd = $from.end()
  if ($from.pos !== paragraphEnd) {
    return false
  }

  const lineText = parent.textContent
  const replacementMarkdown = buildEnterReplacementMarkdown(lineText)
  if (!replacementMarkdown) {
    return false
  }

  const parsedDoc = parser(replacementMarkdown)
  if (parsedDoc.childCount === 0) {
    return false
  }

  const replacement = parsedDoc.content
  const tr = state.tr.replaceWith(paragraphStart - 1, paragraphEnd + 1, replacement)
  view.dispatch(tr.setSelection(TextSelection.near(tr.doc.resolve(paragraphStart), 1)).scrollIntoView())
  return true
}

function buildEnterReplacementMarkdown(lineText: string): string | null {
  const trimmedLine = lineText.trim()
  if (trimmedLine === '---') {
    return '---\n\n'
  }

  const tableMarkdown = buildTableMarkdownFromShortcut(trimmedLine)
  if (tableMarkdown) {
    return tableMarkdown
  }

  const codeFenceMatch = trimmedLine.match(代码围栏起始正则)
  if (codeFenceMatch) {
    const language = codeFenceMatch[2] ?? ''
    return `\`\`\`${language}\n\n\`\`\`\n`
  }

  return null
}

function buildTableMarkdownFromShortcut(lineText: string): string | null {
  const match = lineText.match(表格简写正则)
  if (!match) {
    return null
  }

  const columns = match[1]
    .split('|')
    .map((column) => column.trim())
    .filter((column) => column.length > 0)
  if (columns.length < 2) {
    return null
  }

  const header = `| ${columns.join(' | ')} |`
  const separator = `| ${columns.map(() => '---').join(' | ')} |`
  const body = `| ${columns.map(() => '').join(' | ')} |`
  return `${header}\n${separator}\n${body}\n`
}

function handleMarkdownBackspace(view: EditorView, listItemType: ProseNode['type']): boolean {
  const { state } = view
  const { selection } = state
  if (!(selection instanceof TextSelection) || !selection.empty) {
    return false
  }

  const { $from } = selection
  if ($from.parentOffset !== 0 || !isTextBlockInNestedListItem($from)) {
    return false
  }

  return liftListItem(listItemType)(state, view.dispatch, view)
}

function isTextBlockInNestedListItem($from: TextSelection['$from']): boolean {
  let closestListItemDepth = -1
  let listItemAncestorCount = 0

  for (let depth = $from.depth; depth > 0; depth -= 1) {
    const node = $from.node(depth)
    if (node.type.name !== 'list_item') {
      continue
    }

    listItemAncestorCount += 1
    if (closestListItemDepth === -1) {
      closestListItemDepth = depth
    }
  }

  if (closestListItemDepth === -1 || listItemAncestorCount < 2) {
    return false
  }

  return $from.parent === $from.node(closestListItemDepth).firstChild
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

function buildExtendedMarkdownDecorations(doc: ProseNode): DecorationSet {
  const decorations: Decoration[] = []
  const textBlocks: MarkdownTextBlock[] = []

  doc.descendants((node, pos) => {
    if (node.type.name === 'blockquote') {
      addGithubAlertBlockDecoration(node, pos, decorations)
      return true
    }

    if (!node.isTextblock || node.type.spec.code) {
      return true
    }

    const text = node.textContent
    const from = pos + 1
    textBlocks.push({
      node,
      pos,
      from,
      to: from + text.length,
      text,
    })
    addBlockMathFenceDecoration(text, from, decorations)
    addRegexDecorations(text, from, 缩写定义正则, 'milkdown-extended-markdown-token--abbr', decorations)
    addRegexDecorations(text, from, Emoji短码正则, 'milkdown-extended-markdown-token--emoji', decorations, (match) => {
      return match[0] !== ':spoiler' && !text.startsWith(':spoiler[', match.index)
    })
    addSpoilerDecorations(text, from, decorations)
    addInlineMathDecorations(text, from, decorations)
    addGithubCardDecorations(text, from, decorations)
    addGithubAlertTitleDecoration(text, from, decorations)
    return true
  })

  addBlockMathContentDecorations(textBlocks, decorations)
  return DecorationSet.create(doc, decorations)
}

function addGithubAlertBlockDecoration(
  node: ProseNode,
  pos: number,
  decorations: Decoration[],
) {
  const firstChild = node.firstChild
  if (!firstChild?.isTextblock) {
    return
  }

  const match = firstChild.textContent.match(/^\\?\[!([A-Za-z][\w-]*)](.*)$/)
  if (!match) {
    return
  }

  const type = match[1].toUpperCase()
  if (!GitHub提示块类型集合.has(type)) {
    return
  }

  decorations.push(Decoration.node(pos, pos + node.nodeSize, {
    class: `milkdown-extended-markdown-alert milkdown-extended-markdown-alert--${type.toLowerCase()}`,
    'data-alert-type': type,
  }))
}

function addGithubAlertTitleDecoration(
  text: string,
  from: number,
  decorations: Decoration[],
) {
  GitHub提示块正则.lastIndex = 0
  for (const match of text.matchAll(GitHub提示块正则)) {
    const type = match[1].toUpperCase()
    if (!GitHub提示块类型集合.has(type)) {
      continue
    }

    decorations.push(Decoration.inline(
      from + match.index,
      from + match.index + match[0].length,
      {
        class: 'milkdown-extended-markdown-token milkdown-extended-markdown-token--alert',
        'data-alert-type': type,
      },
    ))
  }
}

function addBlockMathFenceDecoration(
  text: string,
  from: number,
  decorations: Decoration[],
) {
  const trimmedText = text.trim()
  if (trimmedText !== '$$' && !转义块级数学围栏正则.test(trimmedText)) {
    return
  }

  decorations.push(Decoration.inline(from, from + text.length, {
    class: 'milkdown-extended-markdown-token milkdown-extended-markdown-token--math-fence',
  }))
}

function addBlockMathContentDecorations(
  textBlocks: MarkdownTextBlock[],
  decorations: Decoration[],
) {
  let mathBlockStart: MarkdownTextBlock | null = null

  for (const block of textBlocks) {
    const isFence = isBlockMathFence(block.text)
    if (isFence) {
      mathBlockStart = mathBlockStart ? null : block
      continue
    }

    if (!mathBlockStart) {
      continue
    }

    decorations.push(Decoration.node(block.pos, block.pos + block.node.nodeSize, {
      class: 'milkdown-extended-markdown-block-math',
    }))
  }
}

function isBlockMathFence(text: string): boolean {
  const trimmedText = text.trim()
  return trimmedText === '$$' || 转义块级数学围栏正则.test(trimmedText)
}

function addRegexDecorations(
  text: string,
  from: number,
  regex: RegExp,
  className: string,
  decorations: Decoration[],
  predicate?: (match: RegExpMatchArray & { index: number }) => boolean,
) {
  regex.lastIndex = 0
  for (const match of text.matchAll(regex)) {
    if (predicate && !predicate(match as RegExpMatchArray & { index: number })) {
      continue
    }

    decorations.push(Decoration.inline(
      from + match.index,
      from + match.index + match[0].length,
      { class: `milkdown-extended-markdown-token ${className}` },
    ))
  }
}

function addSpoilerDecorations(text: string, from: number, decorations: Decoration[]) {
  剧透文本正则.lastIndex = 0
  for (const match of text.matchAll(剧透文本正则)) {
    const content = match[1] ?? ''
    const openingBracketIndex = match[0].indexOf('[')
    if (openingBracketIndex === -1) {
      continue
    }

    const contentStart = match.index + openingBracketIndex + 1
    const contentEnd = contentStart + content.length

    decorations.push(Decoration.inline(from + match.index, from + contentStart, {
      class: 'milkdown-extended-markdown-syntax-hidden',
    }))
    if (contentEnd > contentStart) {
      decorations.push(Decoration.inline(
        from + contentStart,
        from + contentEnd,
        { class: 'milkdown-extended-markdown-spoiler' },
      ))
    }
    decorations.push(Decoration.inline(from + contentEnd, from + match.index + match[0].length, {
      class: 'milkdown-extended-markdown-syntax-hidden',
    }))
  }
}

function addInlineMathDecorations(text: string, from: number, decorations: Decoration[]) {
  行内数学正则.lastIndex = 0
  for (const match of text.matchAll(行内数学正则)) {
    const leadingTextLength = match[1]?.length ?? 0
    const start = match.index + leadingTextLength
    const end = start + match[0].length - leadingTextLength
    decorations.push(Decoration.inline(from + start, from + end, {
      class: 'milkdown-extended-markdown-token milkdown-extended-markdown-token--math',
    }))
  }
}

function addGithubCardDecorations(text: string, from: number, decorations: Decoration[]) {
  GitHub卡片正则.lastIndex = 0
  for (const match of text.matchAll(GitHub卡片正则)) {
    decorations.push(Decoration.inline(
      from + match.index,
      from + match.index + match[0].length,
      {
        class: 'milkdown-extended-markdown-token milkdown-extended-markdown-token--github-card',
        'data-github-repo': match[1],
      },
    ))
  }
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
      ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
        if (isApplyingExternalMarkdown.value || !isEditorReadyForLocalUpdates.value) {
          return
        }

        const normalizedMarkdown = normalizeSerializedMarkdown(markdown)
        isMilkdownContentPristine.value = false
        lastMarkdown.value = normalizedMarkdown
        emit('update:modelValue', normalizedMarkdown)
      })
    })
    .use(commonmarkEditorPlugins)
    .use(gfm)
    .use(markdownLinkInputRule)
    .use(reverseInlineMarkdownInput)
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
    isMilkdownContentPristine.value = true
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

  if (!isSourceMode.value && isMilkdownContentPristine.value) {
    return lastMarkdown.value
  }

  return currentEditor.action((ctx) => {
    const view = ctx.get(editorViewCtx)
    const serializer = ctx.get(serializerCtx)
    return normalizeSerializedMarkdown(serializer(view.state.doc))
  })
}

function normalizeSerializedMarkdown(markdown: string): string {
  return markdown
    .replace(标签页压缩代码块正则, (_match, title: string, language: string, content: string) => {
      const fence = '```'
      const normalizedContent = content.trim()
      return [
        `=== "${title}"`,
        `    ${fence}${language}`,
        `    ${normalizedContent}`,
        `    ${fence}`,
      ].join('\n')
    })
    .replace(标签页标题转义正则, '$1')
    .replace(转义块级数学围栏全局正则, () => '$$')
    .replace(转义行内数学正则, (_match, prefix: string, content: string) => `${prefix}$${content}$`)
    .replace(转义缩写定义正则, '*[$1]:$2')
    .replace(转义GitHub提示块正文正则, '[!$1]')
    .replace(转义剧透文本正则, ':spoiler[$1]')
    .replace(转义GitHub卡片正则, '::github{repo="$1"}')
    .replace(转义Emoji短码正则, ':$1:')
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
  isMilkdownContentPristine.value = true
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
  isMilkdownContentPristine.value = false
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

function focus() {
  if (isSourceMode.value) {
    sourceTextareaRef.value?.focus()
    return
  }

  getEditorView()?.focus()
}

function handleSourceInput() {
  lastMarkdown.value = sourceContent.value
  updateCursorStatus()
  emit('update:modelValue', sourceContent.value)
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

function toggleToolbarDropdown(item: ToolbarItem, index: number, event: MouseEvent) {
  const itemKey = getToolbarItemKey(item, index)
  if (activeDropdownKey.value === itemKey) {
    closeToolbarDropdown()
    return
  }

  openToolbarDropdown(item, index, event)
}

function openToolbarDropdown(item: ToolbarItem, index: number, event: MouseEvent | FocusEvent) {
  const target = event.currentTarget
  if (!(target instanceof HTMLElement)) {
    return
  }

  const rect = target.getBoundingClientRect()
  activeDropdownKey.value = getToolbarItemKey(item, index)
  activeDropdownStyle.value = {
    left: `${rect.left}px`,
    top: `${rect.bottom + 4}px`,
  }
}

function closeToolbarDropdown() {
  activeDropdownKey.value = ''
}

function handleDocumentPointerDown(event: PointerEvent) {
  const target = event.target
  if (!(target instanceof Element)) {
    return
  }

  if (
    target.closest('.milkdown-markdown-editor__toolbar-dropdown')
    || target.closest('.milkdown-markdown-editor__toolbar-menu')
  ) {
    return
  }

  closeToolbarDropdown()
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

  if (action === 'pageFullscreen') {
    togglePageFullscreen()
    return
  }

  if (action === 'fullscreen') {
    void toggleScreenFullscreen()
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

  isMilkdownContentPristine.value = false
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
    case 'strong':
    case 'emphasis':
    case 'strikethrough':
    case 'inlineCode':
    case 'link':
    case 'mermaid':
    case 'math':
      insertMarkdown(buildToolbarMarkdownSnippet(action, payload))
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
    case 'format':
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
    case 'inlineCode':
      return '`代码`'
    case 'link':
      return '[链接文本](https://example.com)'
    case 'mermaid':
      return buildMermaidSnippet(String(payload ?? 'flow'))
    case 'math':
      return payload === 'block' ? '\n$$\nE = mc^2\n$$\n' : '$E = mc^2$'
    default:
      return ''
  }
}

function buildMermaidSnippet(type: string): string {
  const snippets: Record<string, string> = {
    flow: 'graph TD\n  A[开始] --> B[结束]',
    sequence: 'sequenceDiagram\n  Alice->>Bob: 你好\n  Bob-->>Alice: 收到',
    gantt: 'gantt\n  title 计划\n  dateFormat  YYYY-MM-DD\n  任务一 :a1, 2026-01-01, 3d',
    class: 'classDiagram\n  class Article\n  Article : string title',
    state: 'stateDiagram-v2\n  [*] --> 草稿\n  草稿 --> 发布',
    pie: 'pie title 占比\n  "写作" : 60\n  "整理" : 40',
    relationship: 'erDiagram\n  ARTICLE ||--o{ TAG : has',
    journey: 'journey\n  title 写作流程\n  section 准备\n    构思: 5: 我',
  }
  return `\n\`\`\`mermaid\n${snippets[type] ?? snippets.flow}\n\`\`\`\n`
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
  getScrollElement,
  getScrollRatio,
  setScrollRatio,
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
      <div class="milkdown-markdown-editor__toolbar-scroll">
        <template v-for="(item, itemIndex) in toolbarItems" :key="getToolbarItemKey(item, itemIndex)">
          <span
            v-if="item.type === 'separator'"
            class="milkdown-markdown-editor__toolbar-separator"
            aria-hidden="true"
          />
          <span
            v-else-if="item.type === 'spacer'"
            class="milkdown-markdown-editor__toolbar-spacer"
            aria-hidden="true"
          />
          <div
            v-else-if="item.type === 'dropdown'"
            v-show="!item.hidden?.()"
            class="milkdown-markdown-editor__toolbar-dropdown"
            @focusin="openToolbarDropdown(item, itemIndex, $event)"
          >
            <button
              class="milkdown-markdown-editor__toolbar-button"
              type="button"
              :class="{ 'is-active': item.active?.() }"
              :title="item.title"
              :aria-label="item.title"
              :aria-pressed="item.active?.()"
              :disabled="item.disabled?.()"
              @click="toggleToolbarDropdown(item, itemIndex, $event)"
            >
              <component
                :is="item.icon"
                v-if="item.icon"
                class="milkdown-markdown-editor__toolbar-icon"
                aria-hidden="true"
              />
            </button>
            <div
              v-if="activeDropdownKey === getToolbarItemKey(item, itemIndex)"
              class="milkdown-markdown-editor__toolbar-menu"
              :class="{ 'milkdown-markdown-editor__toolbar-menu--table': item.action === 'table' }"
              :style="activeDropdownStyle"
            >
              <template v-if="item.action === 'table'">
                <div class="milkdown-markdown-editor__table-size-label">
                  {{ hoveredTableRows }} x {{ hoveredTableCols }}
                </div>
                <div class="milkdown-markdown-editor__table-size-grid">
                  <div
                    v-for="row in 表格行列选项"
                    :key="`row-${row}`"
                    class="milkdown-markdown-editor__table-size-row"
                  >
                    <button
                      v-for="col in 表格行列选项"
                      :key="`${row}-${col}`"
                      class="milkdown-markdown-editor__table-size-cell"
                      type="button"
                      :title="`${row} x ${col}`"
                      :class="{
                        'is-active': row <= hoveredTableRows && col <= hoveredTableCols,
                      }"
                      @mouseenter="hoveredTableRows = row; hoveredTableCols = col"
                      @focus="hoveredTableRows = row; hoveredTableCols = col"
                      @click="runToolbarAction('table', `${row}x${col}`); closeToolbarDropdown()"
                    />
                  </div>
                </div>
              </template>
              <template v-else>
                <button
                  v-for="option in item.dropdown"
                  :key="`${option.action}-${option.payload ?? option.label}`"
                  class="milkdown-markdown-editor__toolbar-menu-item"
                  type="button"
                  :title="option.title"
                  @click="runToolbarAction(option.action, option.payload); closeToolbarDropdown()"
                >
                  {{ option.label }}
                </button>
              </template>
            </div>
          </div>
          <button
            v-else
            v-show="!item.hidden?.()"
            class="milkdown-markdown-editor__toolbar-button"
            type="button"
            :class="{ 'is-active': item.active?.() }"
            :title="item.title"
            :aria-label="item.title"
            :aria-pressed="item.active?.()"
            :disabled="item.disabled?.()"
            @click="item.action && runToolbarAction(item.action)"
          >
            <component
              :is="item.icon"
              v-if="item.icon"
              class="milkdown-markdown-editor__toolbar-icon"
              aria-hidden="true"
            />
            <span
              v-else
              class="milkdown-markdown-editor__toolbar-text"
              :class="`milkdown-markdown-editor__toolbar-text--${item.action}`"
            >
              {{ item.label }}
            </span>
          </button>
        </template>
        <span v-if="isUploading" class="milkdown-markdown-editor__toolbar-tip">图片上传中...</span>
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
        @click="updateSourceSelectionStatus"
        @keyup="updateSourceSelectionStatus"
        @select="updateSourceSelectionStatus"
      />
      <div v-if="loading" class="milkdown-markdown-editor__loading">
        正在加载编辑器...
      </div>
    </div>

    <div class="milkdown-markdown-editor__footer">
      <div class="milkdown-markdown-editor__footer-left">
        <span class="milkdown-markdown-editor__footer-item">{{ editorModeLabel }}</span>
      </div>
      <div class="milkdown-markdown-editor__footer-right">
        <span class="milkdown-markdown-editor__footer-item">当前行 {{ cursorStatus.line }}</span>
        <span
          v-if="cursorStatus.selectedCharacters > 0"
          class="milkdown-markdown-editor__footer-item"
        >
          已选择 {{ cursorStatus.selectedWords }} 字 / {{ cursorStatus.selectedCharacters }} 字符
        </span>
        <span class="milkdown-markdown-editor__footer-item">共 {{ editorStats.lines }} 行</span>
        <span class="milkdown-markdown-editor__footer-item">{{ editorStats.words }} 字</span>
        <span class="milkdown-markdown-editor__footer-item">{{ editorStats.characters }} 字符</span>
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
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
  color: var(--el-text-color-primary);
}

.milkdown-markdown-editor__toolbar {
  display: flex;
  align-items: center;
  min-height: 35px;
  padding: 4px 8px;
  box-sizing: border-box;
  border-bottom: 1px solid color-mix(in srgb, var(--el-border-color) 82%, transparent);
  background: var(--milkdown-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-toolbar-bg-color, var(--el-bg-color-overlay));
  overflow: visible;
}

.milkdown-markdown-editor__toolbar-scroll {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  overflow-x: auto;
  overflow-y: visible;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__toolbar-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
  flex: 0 0 auto;
  transition:
    background-color 0.16s ease,
    color 0.16s ease;
}

.milkdown-markdown-editor__toolbar-button:hover {
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar-button.is-active {
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__toolbar-button:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--el-color-primary) 40%, transparent);
  outline-offset: 1px;
}

.milkdown-markdown-editor__toolbar-button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.milkdown-markdown-editor__toolbar-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2;
}

.milkdown-markdown-editor__toolbar-text {
  font-weight: 700;
  font-family: Arial, Helvetica, sans-serif;
}

.milkdown-markdown-editor__toolbar-text--emphasis {
  font-style: italic;
}

.milkdown-markdown-editor__toolbar-text--strikethrough {
  text-decoration: line-through;
}

.milkdown-markdown-editor__toolbar-tip {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.milkdown-markdown-editor__toolbar-separator {
  display: inline-block;
  flex: 0 0 auto;
  width: 1px;
  height: 18px;
  margin: 0 6px;
  background: color-mix(in srgb, var(--el-border-color) 76%, transparent);
}

.milkdown-markdown-editor__toolbar-spacer {
  flex: 1 1 auto;
  min-width: 12px;
}

.milkdown-markdown-editor__toolbar-dropdown {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
}

.milkdown-markdown-editor__toolbar-menu {
  position: fixed;
  z-index: 4000;
  min-width: 116px;
  padding: 6px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  background: var(--el-bg-color-overlay);
  box-shadow: var(--el-box-shadow-light);
}

.milkdown-markdown-editor__toolbar-menu--table {
  min-width: 172px;
}

.milkdown-markdown-editor__toolbar-menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 28px;
  padding: 0 10px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  font-size: 13px;
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
}

.milkdown-markdown-editor__toolbar-menu-item:hover,
.milkdown-markdown-editor__toolbar-menu-item:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__table-size-label {
  margin-bottom: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
  text-align: center;
}

.milkdown-markdown-editor__table-size-grid {
  display: grid;
  gap: 4px;
}

.milkdown-markdown-editor__table-size-row {
  display: grid;
  grid-template-columns: repeat(6, 18px);
  gap: 4px;
  padding: 0;
  border: none;
  background: transparent;
}

.milkdown-markdown-editor__table-size-cell {
  width: 18px;
  height: 18px;
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
  border-radius: 2px;
  background: var(--el-bg-color);
  cursor: pointer;
}

.milkdown-markdown-editor__table-size-cell.is-active {
  border-color: var(--el-color-primary);
  background: color-mix(in srgb, var(--el-color-primary) 18%, var(--el-bg-color));
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
  background: color-mix(
    in srgb,
    var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay)) 86%,
    transparent
  );
  backdrop-filter: blur(3px);
}

.milkdown-markdown-editor__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 24px;
  padding: 0 10px;
  box-sizing: border-box;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 72%, transparent);
  background: var(--milkdown-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-toolbar-bg-color, var(--el-bg-color-overlay));
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1;
}

.milkdown-markdown-editor__footer-left,
.milkdown-markdown-editor__footer-right {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.milkdown-markdown-editor__footer-right {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.milkdown-markdown-editor__footer-item {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  white-space: nowrap;
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

.milkdown-markdown-editor :deep(.ProseMirror ul),
.milkdown-markdown-editor :deep(.ProseMirror ol) {
  margin: 0 0 0.85em;
  padding-inline-start: 1.65em;
  list-style-position: outside;
}

.milkdown-markdown-editor :deep(.ProseMirror ul) {
  list-style-type: disc;
}

.milkdown-markdown-editor :deep(.ProseMirror ul ul) {
  list-style-type: circle;
}

.milkdown-markdown-editor :deep(.ProseMirror ul ul ul) {
  list-style-type: square;
}

.milkdown-markdown-editor :deep(.ProseMirror ol) {
  list-style-type: decimal;
}

.milkdown-markdown-editor :deep(.ProseMirror ol ol) {
  list-style-type: lower-alpha;
}

.milkdown-markdown-editor :deep(.ProseMirror ol ol ol) {
  list-style-type: lower-roman;
}

.milkdown-markdown-editor :deep(.ProseMirror li) {
  margin: 0.18em 0;
  padding-inline-start: 0.18em;
}

.milkdown-markdown-editor :deep(.ProseMirror li > p) {
  margin: 0.08em 0;
}

.milkdown-markdown-editor :deep(.ProseMirror li > ul),
.milkdown-markdown-editor :deep(.ProseMirror li > ol) {
  margin: 0.28em 0 0;
  padding-inline-start: 1.7em;
}

.milkdown-markdown-editor :deep(.ProseMirror li::marker) {
  color: var(--el-color-primary);
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

.milkdown-markdown-editor :deep(.ProseMirror li[data-item-type="task"]) {
  position: relative;
  list-style: none;
}

.milkdown-markdown-editor :deep(.ProseMirror li[data-item-type="task"]::before) {
  content: '';
  position: absolute;
  top: 0.48em;
  left: -1.35em;
  width: 0.92em;
  height: 0.92em;
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
  border-radius: 3px;
  background: var(--el-bg-color);
}

.milkdown-markdown-editor :deep(.ProseMirror li[data-item-type="task"][data-checked="true"]::before) {
  border-color: var(--el-color-primary);
  background:
    linear-gradient(135deg, transparent 0 45%, #fff 45% 55%, transparent 55%) 36% 58% / 42% 42% no-repeat,
    linear-gradient(45deg, transparent 0 45%, #fff 45% 55%, transparent 55%) 62% 48% / 52% 52% no-repeat,
    var(--el-color-primary);
}

.milkdown-markdown-editor :deep(.ProseMirror li[data-item-type="task"][data-checked="true"]) {
  color: var(--el-text-color-secondary);
}

.milkdown-markdown-editor :deep(.ProseMirror img) {
  max-width: 100%;
  border-radius: 8px;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token) {
  border-radius: 4px;
  padding: 1px 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  font-size: 0.92em;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--abbr) {
  background: color-mix(in srgb, var(--el-color-info) 12%, transparent);
  color: var(--el-color-info);
  text-decoration: underline dotted;
  text-underline-offset: 0.2em;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--emoji) {
  background: color-mix(in srgb, var(--el-color-warning) 14%, transparent);
  color: var(--el-color-warning);
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--math),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--math-fence) {
  background: color-mix(in srgb, var(--el-color-primary) 12%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--math-fence) {
  display: inline-block;
  min-width: 2.3em;
  text-align: center;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-block-math) {
  margin: 0.35em 0 0.85em;
  border-radius: 8px;
  padding: 0.65em 0.85em;
  background: color-mix(in srgb, var(--el-color-primary) 8%, transparent);
  color: var(--el-color-primary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  text-align: center;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-syntax-hidden) {
  font-size: 0;
  opacity: 0;
  user-select: none;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-spoiler) {
  border-radius: 4px;
  background: var(--el-fill-color-darker);
  color: transparent;
  text-shadow: 0 0 7px color-mix(in srgb, var(--el-text-color-primary) 72%, transparent);
  transition:
    color 0.15s ease,
    text-shadow 0.15s ease;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-spoiler:hover) {
  color: var(--el-text-color-primary);
  text-shadow: none;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert) {
  --milkdown-alert-accent: var(--el-color-primary);
  border-left-color: var(--milkdown-alert-accent);
  border-radius: 8px;
  padding: 0.35em 0 0.35em 1em;
  background: color-mix(in srgb, var(--milkdown-alert-accent) 7%, transparent);
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--tip),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--success),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--check),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--done) {
  --milkdown-alert-accent: var(--el-color-success);
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--warning),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--caution),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--attention),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--question),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--help),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--faq) {
  --milkdown-alert-accent: var(--el-color-warning);
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--failure),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--missing),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--fail),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--danger),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--error),
.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert--bug) {
  --milkdown-alert-accent: var(--el-color-danger);
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--alert) {
  background: color-mix(in srgb, var(--milkdown-alert-accent, var(--el-color-primary)) 12%, transparent);
  color: var(--milkdown-alert-accent, var(--el-color-primary));
  font-weight: 700;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--github-card) {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  border: 1px solid color-mix(in srgb, var(--el-border-color) 120%, transparent);
  border-radius: 6px;
  padding: 2px 8px;
  background: color-mix(in srgb, var(--el-fill-color-light) 70%, transparent);
  color: transparent;
  font-size: 0;
  vertical-align: baseline;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-token--github-card::before) {
  content: 'GitHub ' attr(data-github-repo);
  color: var(--el-text-color-primary);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
}

.milkdown-markdown-editor--dark {
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
}

.milkdown-markdown-editor--dark .milkdown-markdown-editor__toolbar-button {
  color: var(--el-text-color-primary);
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

  .milkdown-markdown-editor__toolbar {
    align-items: stretch;
  }

  .milkdown-markdown-editor :deep(.ProseMirror),
  .milkdown-markdown-editor__source {
    padding: 16px;
  }

  .milkdown-markdown-editor__footer {
    align-items: flex-start;
    flex-direction: column;
    gap: 0;
    padding: 2px 10px;
  }

  .milkdown-markdown-editor__footer-right {
    justify-content: flex-start;
  }
}
</style>
