<script setup lang="ts">
import {
  commandsCtx,
  defaultValueCtx,
  Editor,
  editorViewCtx,
  parserCtx,
  remarkStringifyOptionsCtx,
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
import { markRule } from '@milkdown/prose'
import { redo, undo } from '@milkdown/prose/history'
import { InputRule } from '@milkdown/prose/inputrules'
import type { MarkType, Node as ProseNode } from '@milkdown/prose/model'
import { liftListItem } from '@milkdown/prose/schema-list'
import { Plugin, TextSelection } from '@milkdown/prose/state'
import { Decoration, DecorationSet, type EditorView } from '@milkdown/prose/view'
import type { MarkdownNode, Parser } from '@milkdown/transformer'
import { $inputRule, $markAttr, $markSchema, $prose, $remark, insert, replaceAll } from '@milkdown/utils'
import fullEmojiMap from 'markdown-it-emoji/lib/data/full.mjs'
import lightEmojiMap from 'markdown-it-emoji/lib/data/light.mjs'
import emojiShortcutsMap from 'markdown-it-emoji/lib/data/shortcuts.mjs'
import type { Handle } from 'mdast-util-to-markdown'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Markdown提示块大写类型集合,
  Markdown自定义语法Schema,
} from '../markdown-schema'
import MilkdownMarkdown工具栏 from './MilkdownMarkdown工具栏/MilkdownMarkdown工具栏.vue'
import { 创建MilkdownMarkdown工具栏项 } from './MilkdownMarkdown工具栏/创建MilkdownMarkdown工具栏项'
import type {
  ToolbarAction,
  ToolbarItem,
  ToolbarOverflowMenuEntry,
} from './MilkdownMarkdown工具栏/MilkdownMarkdown工具栏类型'
import { 使用MilkdownMarkdown工具栏折叠 } from './MilkdownMarkdown工具栏/使用MilkdownMarkdown工具栏折叠'
import { 使用MilkdownMarkdown工具栏菜单 } from './MilkdownMarkdown工具栏/使用MilkdownMarkdown工具栏菜单'

declare module 'mdast-util-to-markdown' {
  interface ConstructNameMap {
    highlight: 'highlight'
  }
}

type 可变Markdown节点 = MarkdownNode & {
  type: string
  children?: 可变Markdown节点[]
  data?: {
    isInline?: boolean
  }
  lang?: unknown
  meta?: unknown
  value?: unknown
}

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
const isUploading = ref(false)
const imageCropDialogVisible = ref(false)
const imageCropPreviewUrl = ref('')
const imageCropSourceFile = ref<File | null>(null)
const imageCropNaturalSize = ref({ width: 0, height: 0 })
const imageCropRect = ref({ x: 0.08, y: 0.08, width: 0.84, height: 0.84 })
const imageCropStageRef = ref<HTMLDivElement | null>(null)
const syntaxDialogVisible = ref(false)
const syntaxDialogTitle = ref('')
const syntaxDialogContent = ref('')
const githubCardDialogVisible = ref(false)
const githubCardRepoInputRef = ref<HTMLInputElement | null>(null)
const githubCardRepoInput = ref('')
const githubCardRepoError = ref('')
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
let pendingScrollRatioAfterModeSwitch: number | null = null

const highlightAttr = $markAttr('highlight')
const highlightMarkdownHandler: Handle = (node, _parent, state, info) => {
  const marker = '=='
  const exit = state.enter('highlight')
  const tracker = state.createTracker(info)
  let value = tracker.move(marker)
  value += tracker.move(
    state.containerPhrasing(node, {
      before: value,
      after: marker,
      ...tracker.current(),
    }),
  )
  value += tracker.move(marker)
  exit()
  return value
}
const softLineBreakMarkdownHandler: Handle = () => '\n'
const codeFenceInfoMarkdownHandler: Handle = (node, _parent, state, info) => {
  const codeNode = node as 可变Markdown节点
  const language = typeof codeNode.lang === 'string' ? codeNode.lang.trim() : ''
  const meta = typeof codeNode.meta === 'string' ? codeNode.meta.trim() : ''
  const fenceInfo = 清理代码块信息文本([language, meta].filter(Boolean).join(' '))
  const parsedInfo = 拆分代码块信息文本(fenceInfo)
  const marker = '`'
  const raw = String(codeNode.value ?? '')
  const sequence = marker.repeat(Math.max(计算最长连续字符数量(raw, marker) + 1, 3))
  const exit = state.enter('codeFenced')
  const tracker = state.createTracker(info)
  let value = tracker.move(sequence)

  if (parsedInfo.language) {
    const languageExit = state.enter('codeFencedLangGraveAccent')
    value += tracker.move(state.safe(parsedInfo.language, {
      before: value,
      after: ' ',
      encode: ['`'],
      ...tracker.current(),
    }))
    languageExit()
  }

  if (parsedInfo.language && parsedInfo.metadata) {
    const metaExit = state.enter('codeFencedMetaGraveAccent')
    value += tracker.move(' ')
    value += tracker.move(state.safe(parsedInfo.metadata, {
      before: value,
      after: '\n',
      encode: ['`'],
      ...tracker.current(),
    }))
    metaExit()
  }

  value += tracker.move('\n')
  if (raw) {
    value += tracker.move(`${raw}\n`)
  }
  value += tracker.move(sequence)
  exit()
  return value
}
const highlightSchema = $markSchema('highlight', (ctx) => ({
  inclusive: false,
  parseDOM: [
    { tag: 'mark' },
    {
      tag: 'span[data-markdown-mark="highlight"]',
    },
  ],
  toDOM: (mark) => ['mark', ctx.get(highlightAttr.key)(mark)],
  parseMarkdown: {
    match: (node) => node.type === 'highlight',
    runner: (state, node, markType) => {
      state.openMark(markType)
      state.next(node.children as MarkdownNode[] | undefined)
      state.closeMark(markType)
    },
  },
  toMarkdown: {
    match: (mark) => mark.type.name === 'highlight',
    runner: (state, mark) => {
      state.withMark(mark, 'highlight')
    },
  },
}))
const highlightRemarkPlugin = $remark('highlightMarkdown', () => () => (tree) => {
  transformHighlightMarkdownTextNodes(tree as 可变Markdown节点)
})
const softLineBreakRemarkPlugin = $remark('softLineBreakMarkdown', () => () => (tree) => {
  transformSoftLineBreakMarkdownNodes(tree as 可变Markdown节点)
})
const codeFenceInfoRemarkPlugin = $remark('codeFenceInfoMarkdown', () => () => (tree) => {
  transformCodeFenceInfoMarkdownNodes(tree as 可变Markdown节点)
})
const highlightInputRule = $inputRule((ctx) => markRule(
  /(^|[^\w=])==([^=\n](?:.*?[^=\s])?)==$/,
  highlightSchema.type(ctx),
  {
    updateCaptured: ({ fullMatch, start }) => {
      if (fullMatch.startsWith('==')) {
        return {}
      }

      return {
        fullMatch: fullMatch.slice(1),
        start: start + 1,
      }
    },
  },
))
function configureMarkdownSerializer(ctx: Parameters<MilkdownPlugin>[0]) {
  ctx.update(remarkStringifyOptionsCtx, (options) => ({
    ...options,
    handlers: {
      ...(options.handlers ?? {}),
      break: softLineBreakMarkdownHandler,
      code: codeFenceInfoMarkdownHandler,
      highlight: highlightMarkdownHandler,
    },
  }))
}
const highlightMarkdownPlugins: MilkdownPlugin[] = [
  highlightAttr,
  highlightSchema,
  highlightRemarkPlugin,
  softLineBreakRemarkPlugin,
  codeFenceInfoRemarkPlugin,
  highlightInputRule,
].flat()
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
const 标签页标题内容正则源码 = '(?:[^"\\\\]|\\\\.)+'
const Markdown类型名正则源码 = '[A-Za-z][\\w-]*'
const 图片网格开始标记 = 转义正则文本(Markdown自定义语法Schema.imageGrid.openMarker.slice(1, -1))
const 图片网格结束标记 = 转义正则文本(Markdown自定义语法Schema.imageGrid.closeMarker.slice(1, -1))
const 剧透语法名称 = Markdown自定义语法Schema.spoiler.pattern.match(/^:([a-zA-Z][\w-]*)/)?.[1] ?? 'spoiler'
const GitHub卡片语法名称 = Markdown自定义语法Schema.githubCard.pattern.match(/^::([a-zA-Z][\w-]*)/)?.[1] ?? 'github'
const 剧透语法名正则源码 = 转义正则文本(剧透语法名称)
const GitHub卡片语法名正则源码 = 转义正则文本(GitHub卡片语法名称)
const 表格简写正则 = /^\|(.+)\|\s*$/
const 代码围栏起始正则 = /^(`{3,}|~{3,})([^\r\n`]*)$/
const 标签页标题转义正则 = new RegExp(`^\\\\(===\\s+"${标签页标题内容正则源码}"\\s*)$`, 'gm')
const 标签页压缩代码块正则 = new RegExp(
  `^\\\\===\\s+"(${标签页标题内容正则源码})"\\s*\\n\`([a-zA-Z0-9_-]+)\\s+([^\`\\n]+)\``,
  'gm',
)
const 缩写定义正则 = /^\\?\*\\?\[([^\]\\\n]+)\\?]:(\s+.+)$/gm
const 扩展块标题正则 = new RegExp(`^(\\s*)(!!!|\\?\\?\\?\\+?)\\s+${Markdown类型名正则源码}(?:\\s+.*)?$`)
const 标签页标题正则 = new RegExp(`^(\\s*)===\\s+"${标签页标题内容正则源码}"\\s*$`)
const 容器提示块标题正则 = new RegExp(
  `^(\\s*):::${Markdown类型名正则源码}(?:\\\\?\\[(?:[^\\]\\\\]|\\\\.)*\\\\?])?\\s*$`,
)
const 容器提示块结束正则 = /^\s*:::\s*$/
const 扩展块标题转义正则 = /^(\s*)\\(!!!|\?\?\?\+?|===)(.*)$/
const 容器提示块标题转义正则 = /^(\s*)\\:::(.*)$/
const 容器提示块标题方括号转义正则 = /\\([\][])/g
const 图片网格标记转义正则 = new RegExp(`\\\\\\[(${图片网格开始标记}|${图片网格结束标记})\\\\?]`, 'gi')
const GitHub提示块正则 = new RegExp(`^(?:>\\s*)?\\\\?\\[!(${Markdown类型名正则源码})](.*)$`, 'gm')
const 转义GitHub提示块正文正则 = new RegExp(`\\\\\\[!(${Markdown类型名正则源码})]`, 'g')
const 转义缩写定义正则 = /^\\\*\\?\[([^\]\\\n]+)\\?]:(\s+.+)$/gm
const 转义Emoji短码正则 = /\\?:((?:[a-zA-Z0-9_+-]|\\_)+)\\?:/g
const 转义剧透文本正则 = new RegExp(`\\\\?:${剧透语法名正则源码}\\\\?\\[((?:[^\\]\\\\]|\\\\.)*)\\\\?]`, 'g')
const 转义GitHub卡片正则 = new RegExp(
  `\\\\?:\\\\?:${GitHub卡片语法名正则源码}\\\\?\\{repo=\\\\?"([^"\\\\]+\\/[^"\\\\]+)\\\\?"\\\\?}`,
  'g',
)
const 转义块级数学围栏正则 = /^\\\$\\\$\s*$/
const 转义块级数学围栏全局正则 = /^\\\$\\\$\s*$/gm
const 转义行内数学正则 = /(^|[^\\])\\\$([^$\n]+?)\\\$/g
const 转义图片语法正则 = /\\?!\\?\[((?:\\.|[^\]\\])*)\\?\]\\?\(((?:\\.|[^)\\])*)\\?\)/g
const 代码围栏边界正则 = /^(\s*)(`{3,}|~{3,})/
const 转义代码围栏边界正则 = /^(\s*)\\(`{3,}|~{3,})/
const 星号水平线正则 = /^\s*\*(?:\s+\*){2,}\s*$/
const 星号紧凑水平线正则 = /^\s*\*{3,}\s*$/
const Emoji短码正则 = /:([a-zA-Z0-9_+-]+):/g
const 剧透文本正则 = new RegExp(`\\\\?:${剧透语法名正则源码}\\\\?\\[((?:[^\\]\\\\]|\\\\.)*)\\\\?]`, 'g')
const 行内数学正则 = /(^|[^\\])\$([^$\n]+?)\$/g
const GitHub卡片正则 = new RegExp(
  `\\\\?:\\\\?:${GitHub卡片语法名正则源码}\\\\?\\{repo=\\\\?"([^"\\\\]+\\/[^"\\\\]+)\\\\?"\\\\?}`,
  'g',
)

function 转义正则文本(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

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

type CustomMarkdownSnippet =
  | 'github-alert-note'
  | 'github-alert-tip'
  | 'github-alert-important'
  | 'github-alert-warning'
  | 'github-alert-caution'
  | 'github-alert-syntax'
  | 'container-alert'
  | 'indented-alert'
  | 'details-alert-collapsed'
  | 'details-alert-expanded'
  | 'tabs'
  | 'image-grid'
  | 'github-card'
  | 'code-syntax'
  | 'spoiler'

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
const GitHub提示块中文标题映射: Record<string, string> = {
  NOTE: '说明',
  TIP: '提示',
  IMPORTANT: '重要',
  WARNING: '警告',
  CAUTION: '注意',
  ABSTRACT: '摘要',
  SUMMARY: '总结',
  TLDR: '太长不看',
  INFO: '信息',
  TODO: '待办',
  SUCCESS: '成功',
  CHECK: '检查',
  DONE: '完成',
  QUESTION: '问题',
  HELP: '帮助',
  FAQ: '常见问题',
  ATTENTION: '注意',
  FAILURE: '失败',
  MISSING: '缺失',
  FAIL: '失败',
  DANGER: '危险',
  ERROR: '错误',
  BUG: '缺陷',
  EXAMPLE: '示例',
  QUOTE: '引用',
  CITE: '引用',
}

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
const imageCropStyle = computed(() => ({
  left: `${imageCropRect.value.x * 100}%`,
  top: `${imageCropRect.value.y * 100}%`,
  width: `${imageCropRect.value.width * 100}%`,
  height: `${imageCropRect.value.height * 100}%`,
}))
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

function createMarkdownKeyboardPlugin(parser: Parser, listItemType: ProseNode['type']) {
  return new Plugin({
    props: {
      handleKeyDown(view, event) {
        if (event.isComposing || event.altKey) {
          return false
        }

        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey || event.shiftKey)) {
          event.preventDefault()
          return insertSoftLineBreak(view)
        }

        if (event.shiftKey) {
          return false
        }

        if (event.ctrlKey || event.metaKey) {
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

function insertSoftLineBreak(view: EditorView): boolean {
  const hardbreakType = view.state.schema.nodes.hardbreak
  if (!hardbreakType) {
    return false
  }

  const tr = view.state.tr
    .setMeta('hardbreak', true)
    .replaceSelectionWith(hardbreakType.create())
    .scrollIntoView()
  view.dispatch(tr)
  return true
}

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
  if (isThematicBreakShortcut(lineText)) {
    return replaceParagraphWithThematicBreak(view, paragraphStart, paragraphEnd)
  }

  const codeFenceShortcut = parseCodeFenceShortcut(lineText)
  if (codeFenceShortcut) {
    return replaceParagraphWithCodeBlock(view, paragraphStart, paragraphEnd, codeFenceShortcut.language)
  }

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

function isThematicBreakShortcut(lineText: string): boolean {
  return /^(?:---|\*\*\*|___)$/.test(lineText.trim())
}

function replaceParagraphWithThematicBreak(
  view: EditorView,
  paragraphStart: number,
  paragraphEnd: number,
): boolean {
  const { state } = view
  const hrType = state.schema.nodes.hr
  const paragraphType = state.schema.nodes.paragraph
  if (!hrType || !paragraphType) {
    return false
  }

  const hrNode = hrType.create()
  const nextParagraph = paragraphType.create()
  const replaceFrom = paragraphStart - 1
  const tr = state.tr.replaceWith(replaceFrom, paragraphEnd + 1, [hrNode, nextParagraph])
  const nextParagraphStart = replaceFrom + hrNode.nodeSize + 1
  view.dispatch(
    tr.setSelection(TextSelection.create(tr.doc, nextParagraphStart)).scrollIntoView(),
  )
  return true
}

function parseCodeFenceShortcut(lineText: string): { language: string } | null {
  const codeFenceMatch = lineText.trim().match(代码围栏起始正则)
  if (!codeFenceMatch) {
    return null
  }

  return {
    language: 清理代码块信息文本(codeFenceMatch[2] ?? ''),
  }
}

function replaceParagraphWithCodeBlock(
  view: EditorView,
  paragraphStart: number,
  paragraphEnd: number,
  language: string,
): boolean {
  const { state } = view
  const codeBlockType = state.schema.nodes.code_block
  if (!codeBlockType) {
    return false
  }

  const replaceFrom = paragraphStart - 1
  const codeBlockNode = codeBlockType.create({ language })
  const tr = state.tr.replaceWith(replaceFrom, paragraphEnd + 1, codeBlockNode)
  view.dispatch(
    tr.setSelection(TextSelection.create(tr.doc, replaceFrom + 1)).scrollIntoView(),
  )
  return true
}

function buildEnterReplacementMarkdown(lineText: string): string | null {
  const trimmedLine = lineText.trim()
  const tableMarkdown = buildTableMarkdownFromShortcut(trimmedLine)
  if (tableMarkdown) {
    return tableMarkdown
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

function transformHighlightMarkdownTextNodes(node: 可变Markdown节点): void {
  if (Array.isArray(node.children)) {
    node.children = node.children.flatMap((child) => {
      transformHighlightMarkdownTextNodes(child)
      return splitHighlightMarkdownTextNode(child)
    })
  }
}

function transformSoftLineBreakMarkdownNodes(node: 可变Markdown节点): void {
  if (node.type === 'break' && node.data?.isInline) {
    node.data.isInline = false
  }

  node.children?.forEach((child) => transformSoftLineBreakMarkdownNodes(child))
}

function transformCodeFenceInfoMarkdownNodes(node: 可变Markdown节点): void {
  if (node.type === 'code') {
    const language = typeof node.lang === 'string' ? node.lang.trim() : ''
    const meta = typeof node.meta === 'string' ? node.meta.trim() : ''
    const info = 清理代码块信息文本([language, meta].filter(Boolean).join(' '))
    if (meta) {
      node.lang = info
      node.meta = undefined
    } else {
      const parsedInfo = 拆分代码块信息文本(info)
      node.lang = parsedInfo.language
      node.meta = parsedInfo.metadata || undefined
    }
  }

  node.children?.forEach((child) => transformCodeFenceInfoMarkdownNodes(child))
}

function 清理代码块信息文本(value: string): string {
  return value.replace(/\s+/g, ' ').trim()
}

function 拆分代码块信息文本(value: string): { language: string, metadata: string } {
  const info = 清理代码块信息文本(value)
  const firstSpaceIndex = info.search(/\s/)
  if (firstSpaceIndex === -1) {
    return {
      language: info,
      metadata: '',
    }
  }

  return {
    language: info.slice(0, firstSpaceIndex),
    metadata: info.slice(firstSpaceIndex).trim(),
  }
}

function 计算最长连续字符数量(value: string, character: string): number {
  let longest = 0
  let current = 0

  for (const item of value) {
    if (item === character) {
      current += 1
      longest = Math.max(longest, current)
    } else {
      current = 0
    }
  }

  return longest
}

function splitHighlightMarkdownTextNode(node: 可变Markdown节点): 可变Markdown节点[] {
  if (node.type !== 'text' || typeof node.value !== 'string') {
    return [node]
  }

  const text = String(node.value ?? '')
  const nodes: 可变Markdown节点[] = []
  const regex = /(^|[^\w=])==([^=\n](?:.*?[^=\s])?)==/g
  let lastIndex = 0

  for (const match of text.matchAll(regex)) {
    const fullMatch = match[0]
    const prefix = match[1] ?? ''
    const content = match[2] ?? ''
    const matchIndex = match.index ?? 0
    const highlightStart = matchIndex + prefix.length

    if (highlightStart > lastIndex) {
      nodes.push({
        type: 'text',
        value: text.slice(lastIndex, highlightStart),
      })
    }

    nodes.push({
      type: 'highlight',
      children: [
        {
          type: 'text',
          value: content,
        },
      ],
    })
    lastIndex = matchIndex + fullMatch.length
  }

  if (lastIndex === 0) {
    return [node]
  }

  if (lastIndex < text.length) {
    nodes.push({
      type: 'text',
      value: text.slice(lastIndex),
    })
  }

  return nodes
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
      return match[0] !== `:${剧透语法名称}` && !text.startsWith(`:${剧透语法名称}[`, match.index)
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
  if (!Markdown提示块大写类型集合.has(type)) {
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
    if (!Markdown提示块大写类型集合.has(type)) {
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

function normalizeSerializedMarkdown(markdown: string): string {
  const normalizedMarkdown = markdown
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
    .replace(转义图片语法正则, normalizeSerializedMarkdownImage)
    .replace(转义剧透文本正则, `:${剧透语法名称}[$1]`)
    .replace(转义GitHub卡片正则, `::${GitHub卡片语法名称}{repo="$1"}`)
    .replace(
      转义Emoji短码正则,
      (_match, shortcode: string) => `:${shortcode.replace(/\\_/g, '_')}:`,
    )

  return normalizeSerializedMarkdownBlocks(normalizeSerializedMarkdownMarkers(normalizedMarkdown))
}

function normalizeSerializedMarkdownImage(match: string): string {
  const 图片标记被转义 = match.startsWith('\\!') || match.startsWith('!\\[') || match.includes('\\](') || match.includes('\\]\\(')
  if (!图片标记被转义) {
    return match
  }

  return match.replaceAll(/\\([!()[\]])/g, '$1')
}

function normalizeSerializedMarkdownMarkers(markdown: string): string {
  const lines = markdown.split('\n')
  let fence: { marker: string, length: number, indent: string } | null = null

  return lines.map((line) => {
    const markerLine = normalizeSerializedMarkdownFenceMarker(line)
    const fenceMatch = markerLine.match(代码围栏边界正则)

    if (fence) {
      if (
        fenceMatch
        && fenceMatch[1] === fence.indent
        && fenceMatch[2]?.startsWith(fence.marker.repeat(fence.length))
      ) {
        fence = null
        return markerLine
      }

      return line
    }

    if (fenceMatch) {
      const markerText = fenceMatch[2] ?? ''
      fence = {
        marker: markerText[0] ?? '',
        length: markerText.length,
        indent: fenceMatch[1] ?? '',
      }
      return markerLine
    }

    if (星号水平线正则.test(line) || 星号紧凑水平线正则.test(line)) {
      return `${line.match(/^\s*/)?.[0] ?? ''}---`
    }

    return line.replace(/^(\s*)\*(?=[ \t]+(?:\S|$))/, '$1-')
  }).join('\n')
}

function normalizeSerializedMarkdownBlocks(markdown: string): string {
  const lines = markdown.split('\n')
  const normalizedLines: string[] = []
  let fence: { marker: string, length: number, indent: string } | null = null
  let extendedBlock: { indent: string, bodyIndent: string } | null = null
  let containerBlock: { indent: string } | null = null

  for (const rawLine of lines) {
    const line = normalizeSerializedMarkdownBlockMarkers(rawLine)
    const fenceMatch = line.match(代码围栏边界正则)

    if (fence) {
      const normalizedFenceLine = containerBlock
        ? line
        : normalizeSerializedMarkdownBlockBodyLine(line, extendedBlock)
      normalizedLines.push(normalizedFenceLine)
      if (
        fenceMatch
        && normalizeSerializedMarkdownFenceIndent(fenceMatch[1] ?? '', extendedBlock, containerBlock) === fence.indent
        && fenceMatch[2]?.startsWith(fence.marker.repeat(fence.length))
      ) {
        fence = null
      }
      continue
    }

    if (fenceMatch) {
      const markerText = fenceMatch[2] ?? ''
      const normalizedFenceLine = containerBlock
        ? line
        : normalizeSerializedMarkdownBlockBodyLine(line, extendedBlock)
      const normalizedFenceMatch = normalizedFenceLine.match(代码围栏边界正则)
      fence = {
        marker: markerText[0] ?? '',
        length: markerText.length,
        indent: normalizedFenceMatch?.[1] ?? fenceMatch[1] ?? '',
      }
      normalizedLines.push(normalizedFenceLine)
      continue
    }

    if (containerBlock && 容器提示块结束正则.test(line)) {
      normalizedLines.push(`${containerBlock.indent}:::`)
      containerBlock = null
      continue
    }

    const containerTitleMatch = line.match(容器提示块标题正则)
    if (containerTitleMatch) {
      containerBlock = {
        indent: containerTitleMatch[1] ?? '',
      }
      extendedBlock = null
      normalizedLines.push(line)
      continue
    }

    const blockTitleMatch = line.match(扩展块标题正则) ?? line.match(标签页标题正则)
    if (blockTitleMatch) {
      const indent = blockTitleMatch[1] ?? ''
      extendedBlock = {
        indent,
        bodyIndent: `${indent}    `,
      }
      normalizedLines.push(line)
      continue
    }

    if (line.trim().length === 0) {
      if (!containerBlock) {
        extendedBlock = null
      }
      normalizedLines.push(line)
      continue
    }

    normalizedLines.push(containerBlock ? line : normalizeSerializedMarkdownBlockBodyLine(line, extendedBlock))
  }

  return normalizedLines.join('\n')
}

function normalizeSerializedMarkdownBlockMarkers(line: string): string {
  const normalizedLine = line
    .replace(转义代码围栏边界正则, '$1$2')
    .replace(扩展块标题转义正则, '$1$2$3')
    .replace(容器提示块标题转义正则, '$1:::$2')
    .replace(图片网格标记转义正则, '[$1]')

  if (!/^(\s*):::[A-Za-z][\w-]*/.test(normalizedLine)) {
    return normalizedLine
  }

  return normalizedLine.replace(容器提示块标题方括号转义正则, '$1')
}

function normalizeSerializedMarkdownFenceMarker(line: string): string {
  return line.replace(转义代码围栏边界正则, '$1$2')
}

function normalizeSerializedMarkdownFenceIndent(
  indent: string,
  extendedBlock: { bodyIndent: string } | null,
  containerBlock: { indent: string } | null,
): string {
  if (containerBlock) {
    return indent
  }

  return normalizeSerializedMarkdownBlockBodyLine(indent, extendedBlock)
}

function normalizeSerializedMarkdownBlockBodyLine(
  line: string,
  extendedBlock: { bodyIndent: string } | null,
): string {
  if (!extendedBlock || line.startsWith(extendedBlock.bodyIndent)) {
    return line
  }

  return `${extendedBlock.bodyIndent}${line.trimStart()}`
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
    case 'strong':
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

function normalizeCustomMarkdownSnippet(payload?: string | number): CustomMarkdownSnippet | null {
  if (typeof payload !== 'string') {
    return null
  }

  const snippets: readonly CustomMarkdownSnippet[] = [
    'github-alert-note',
    'github-alert-tip',
    'github-alert-important',
    'github-alert-warning',
    'github-alert-caution',
    'github-alert-syntax',
    'container-alert',
    'indented-alert',
    'details-alert-collapsed',
    'details-alert-expanded',
    'tabs',
    'image-grid',
    'github-card',
    'code-syntax',
    'spoiler',
  ]
  return snippets.includes(payload as CustomMarkdownSnippet) ? payload as CustomMarkdownSnippet : null
}

function buildCustomMarkdownSnippet(type: CustomMarkdownSnippet): string {
  switch (type) {
    case 'github-alert-note':
      return buildGithubAlertSnippet('NOTE')
    case 'github-alert-tip':
      return buildGithubAlertSnippet('TIP')
    case 'github-alert-important':
      return buildGithubAlertSnippet('IMPORTANT')
    case 'github-alert-warning':
      return buildGithubAlertSnippet('WARNING')
    case 'github-alert-caution':
      return buildGithubAlertSnippet('CAUTION')
    case 'github-alert-syntax':
      return ''
    case 'container-alert':
      return '\n:::tip[提示标题]\n这里是容器式提示块内容。\n:::\n'
    case 'indented-alert':
      return '\n!!! note "提示标题"\n    这里是缩进式提示块内容。\n'
    case 'details-alert-collapsed':
      return '\n??? warning "折叠标题"\n    这里是默认收起的折叠块内容。\n'
    case 'details-alert-expanded':
      return '\n???+ info "折叠标题"\n    这里是默认展开的折叠块内容。\n'
    case 'tabs':
      return '\n=== "方案一"\n    这里是方案一内容。\n\n=== "方案二"\n    这里是方案二内容。\n'
    case 'image-grid':
      return '\n[grid]\n![图片一](https://example.com/image-1.png)\n![图片二](https://example.com/image-2.png)\n[/grid]\n'
    case 'code-syntax':
      return ''
    case 'spoiler':
      return ':spoiler[这里是剧透内容]'
    case 'github-card':
      return ''
  }
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

function buildGithubAlertSnippet(type: string): string {
  return `\n> [!${type}]\n> 这里是${获取GitHub提示块中文标题(type)}提示块内容。\n`
}

function buildGithubAlertSyntaxSnippet(): string {
  const commonTypes = ['NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION']
  const otherTypes = Markdown自定义语法Schema.admonitions.types
    .map((item) => item.name.toUpperCase())
    .filter((type) => !commonTypes.includes(type))
  const commonTypeText = commonTypes.map(formatGithubAlertTypeLabel).join('、')
  const otherTypeText = otherTypes.map(formatGithubAlertTypeLabel).join('、')

  return [
    '> [!NOTE]',
    '> GitHub 风格提示块：把 [!TYPE] 放在引用块第一行。',
    '',
    `常用类型：${commonTypeText}`,
    `其他类型：${otherTypeText}`,
    '',
  ].join('\n')
}

function formatGithubAlertTypeLabel(type: string): string {
  return `${获取GitHub提示块中文标题(type)}（${type}）`
}

function 获取GitHub提示块中文标题(type: string): string {
  const normalizedType = type.toUpperCase().replace(/[^A-Z0-9]/g, '')
  return GitHub提示块中文标题映射[normalizedType] ?? type
}

function buildCodeSyntaxSnippet(): string {
  const metadataLines = Markdown自定义语法Schema.codeFence.metadata
    .map((item) => `// ${item.aliases.join('/')}：${item.description}`)
    .join('\n')

  return [
    '',
    '```ts title="代码标题" ln startLine=1 highlight={2,4-5} ins={6} del={7} frame=terminal wrap preserveIndent',
    metadataLines,
    'console.log("增强代码块")',
    '```',
    '',
  ].join('\n')
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
        <span v-if="isUploading" class="milkdown-markdown-editor__footer-uploading">图片上传中...</span>
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

    <div
      v-if="imageCropDialogVisible"
      class="milkdown-markdown-editor__crop-dialog"
      role="dialog"
      aria-modal="true"
      aria-label="裁剪上传图片"
    >
      <div class="milkdown-markdown-editor__crop-panel">
        <div class="milkdown-markdown-editor__crop-header">
          <strong>裁剪上传图片</strong>
          <button
            class="milkdown-markdown-editor__crop-close"
            type="button"
            title="关闭"
            @click="closeImageCropDialog"
          >
            关闭
          </button>
        </div>
        <div class="milkdown-markdown-editor__crop-stage">
          <div
            ref="imageCropStageRef"
            class="milkdown-markdown-editor__crop-frame"
            @pointermove="updateImageCropDrag"
            @pointerup="finishImageCropDrag"
            @pointercancel="finishImageCropDrag"
          >
            <img
              class="milkdown-markdown-editor__crop-image"
              :src="imageCropPreviewUrl"
              alt="待裁剪图片"
              draggable="false"
            >
            <div
              class="milkdown-markdown-editor__crop-rect"
              :style="imageCropStyle"
              @pointerdown.stop.prevent="startImageCropDrag('move', $event)"
            >
              <span class="milkdown-markdown-editor__crop-rect-handle" @pointerdown.stop.prevent="startImageCropDrag('resize', $event)" />
            </div>
          </div>
        </div>
        <div class="milkdown-markdown-editor__crop-footer">
          <span>
            {{ Math.round(imageCropRect.width * imageCropNaturalSize.width) }}
            ×
            {{ Math.round(imageCropRect.height * imageCropNaturalSize.height) }}
          </span>
          <div class="milkdown-markdown-editor__crop-actions">
            <button type="button" @click="resetImageCropRect">重置</button>
            <button type="button" @click="closeImageCropDialog">取消</button>
            <button type="button" class="is-primary" :disabled="isUploading" @click="confirmImageCropUpload">
              上传
            </button>
          </div>
        </div>
      </div>
    </div>

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

.milkdown-markdown-editor__footer-uploading {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.milkdown-markdown-editor__crop-dialog {
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

.milkdown-markdown-editor__crop-panel {
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

.milkdown-markdown-editor__crop-header,
.milkdown-markdown-editor__crop-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-editor__crop-footer {
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-editor__crop-stage {
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

.milkdown-markdown-editor__crop-frame {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  max-height: 488px;
  touch-action: none;
}

.milkdown-markdown-editor__crop-image {
  display: block;
  max-width: 100%;
  max-height: 488px;
  user-select: none;
}

.milkdown-markdown-editor__crop-rect {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid var(--el-color-primary);
  background: rgba(64, 158, 255, 0.12);
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.38);
  cursor: move;
}

.milkdown-markdown-editor__crop-rect-handle {
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

.milkdown-markdown-editor__crop-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.milkdown-markdown-editor__crop-close,
.milkdown-markdown-editor__crop-actions button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__crop-actions button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}

.milkdown-markdown-editor__crop-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
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
  color: var(--milkdown-markdown-text-primary);
  caret-color: var(--milkdown-markdown-text-primary);
  font-size: 15px;
  line-height: 1.75;
  word-break: break-word;
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
  color: var(--milkdown-markdown-primary);
}

.milkdown-markdown-editor :deep(.ProseMirror a) {
  color: var(--milkdown-markdown-primary);
  font-weight: 500;
  text-decoration: underline;
  text-decoration-style: dashed;
  text-decoration-color: color-mix(in srgb, var(--milkdown-markdown-primary) 30%, transparent);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.22em;
}

.milkdown-markdown-editor :deep(.ProseMirror a:hover) {
  background: var(--milkdown-markdown-hover-bg);
  text-decoration: none;
}

.milkdown-markdown-editor :deep(.ProseMirror h1),
.milkdown-markdown-editor :deep(.ProseMirror h2),
.milkdown-markdown-editor :deep(.ProseMirror h3),
.milkdown-markdown-editor :deep(.ProseMirror h4),
.milkdown-markdown-editor :deep(.ProseMirror h5),
.milkdown-markdown-editor :deep(.ProseMirror h6) {
  margin: 1.1em 0 0.55em;
  color: var(--milkdown-markdown-text-primary);
  font-weight: 700;
  line-height: 1.32;
}

.milkdown-markdown-editor :deep(.ProseMirror h1:first-child),
.milkdown-markdown-editor :deep(.ProseMirror h2:first-child),
.milkdown-markdown-editor :deep(.ProseMirror h3:first-child) {
  margin-top: 0;
}

.milkdown-markdown-editor :deep(.ProseMirror blockquote) {
  position: relative;
  margin: 0.85em 0;
  padding: 0.08em 0 0.08em 1em;
  border: 0;
  color: var(--milkdown-markdown-text-primary);
  background: transparent;
}

.milkdown-markdown-editor :deep(.ProseMirror blockquote::before) {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: -0.25rem;
  width: 0.25rem;
  border-radius: 999px;
  background: var(--milkdown-markdown-primary);
}

.milkdown-markdown-editor :deep(.ProseMirror blockquote > :first-child) {
  margin-top: 0;
}

.milkdown-markdown-editor :deep(.ProseMirror blockquote > :last-child) {
  margin-bottom: 0;
}

.milkdown-markdown-editor :deep(.ProseMirror blockquote p) {
  margin: 0.15em 0;
}

.milkdown-markdown-editor :deep(.ProseMirror hr) {
  margin: 1rem 0;
  border: 0;
  border-top: 1px dashed rgba(0, 0, 0, 0.28);
}

.milkdown-markdown-editor :deep(.ProseMirror pre) {
  position: relative;
  overflow: auto;
  margin: 1rem 0;
  padding: 44px 14px 12px;
  border-radius: 8px;
  border: 1px solid var(--milkdown-markdown-border);
  background: var(--milkdown-markdown-soft-bg);
  color: var(--milkdown-markdown-text-primary);
}

.milkdown-markdown-editor :deep(.ProseMirror pre::before) {
  content: attr(data-language);
  position: absolute;
  inset-block-start: 0;
  inset-inline: 0;
  min-height: 32px;
  padding: 7px 12px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--milkdown-markdown-border);
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, var(--milkdown-markdown-card-bg));
  color: var(--milkdown-markdown-text-secondary);
  font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.milkdown-markdown-editor :deep(.ProseMirror pre:not([data-language])::before),
.milkdown-markdown-editor :deep(.ProseMirror pre[data-language='']::before) {
  content: '纯文本';
}

.milkdown-markdown-editor :deep(.ProseMirror code) {
  border-radius: 4px;
  padding: 2px 4px;
  background: var(--milkdown-markdown-inline-code-bg);
  color: var(--milkdown-markdown-inline-code-text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor :deep(.ProseMirror pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}

.milkdown-markdown-editor :deep(.ProseMirror mark) {
  border-radius: 4px;
  padding: 1px 5px;
  background: color-mix(in srgb, var(--milkdown-markdown-primary) 22%, #fff4b5);
  color: var(--milkdown-markdown-text-primary);
}

.milkdown-markdown-editor :deep(.ProseMirror table) {
  width: max-content;
  max-width: 100%;
  border-collapse: collapse;
}

.milkdown-markdown-editor :deep(.ProseMirror th),
.milkdown-markdown-editor :deep(.ProseMirror td) {
  border: 1px solid var(--milkdown-markdown-border);
  padding: 6px 8px;
  color: var(--milkdown-markdown-text-primary);
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
  border: 1px solid var(--milkdown-markdown-border);
  border-radius: 3px;
  background: var(--milkdown-markdown-card-bg);
  cursor: pointer;
}

.milkdown-markdown-editor :deep(.ProseMirror li[data-item-type="task"][data-checked="true"]::before) {
  border-color: var(--milkdown-markdown-primary);
  background:
    linear-gradient(135deg, transparent 0 45%, #fff 45% 55%, transparent 55%) 36% 58% / 42% 42% no-repeat,
    linear-gradient(45deg, transparent 0 45%, #fff 45% 55%, transparent 55%) 62% 48% / 52% 52% no-repeat,
    var(--milkdown-markdown-primary);
}

.milkdown-markdown-editor :deep(.ProseMirror li[data-item-type="task"][data-checked="true"]) {
  color: var(--milkdown-markdown-text-secondary);
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
  color: var(--milkdown-markdown-text-primary);
  text-shadow: none;
}

.milkdown-markdown-editor :deep(.milkdown-extended-markdown-alert) {
  --milkdown-alert-accent: var(--el-color-primary);
  border-left-color: var(--milkdown-alert-accent);
  border-radius: 8px;
  padding: 0.18em 0 0.18em 0.9em;
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
  color: var(--milkdown-markdown-text-primary);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.milkdown-markdown-editor :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  color: var(--milkdown-markdown-text-tertiary);
  pointer-events: none;
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

.milkdown-markdown-editor--dark :deep(.ProseMirror mark) {
  background: color-mix(in srgb, var(--milkdown-markdown-primary) 20%, rgba(250, 204, 21, 0.28));
}

.milkdown-markdown-editor--dark :deep(.ProseMirror hr) {
  border-top-color: rgba(255, 255, 255, 0.28);
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
