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
import {
  ArrowDownUp,
  Blocks,
  Bold,
  ChartArea,
  Code,
  Expand,
  EyeOff,
  FileCode,
  FilePenLine,
  Forward,
  Github,
  Heading,
  Highlighter,
  Image,
  Italic,
  LayoutPanelTop,
  Link,
  List,
  ListOrdered,
  ListTodo,
  Maximize2,
  Pilcrow,
  Quote,
  Reply,
  SeparatorHorizontal,
  Smile,
  SquareCode,
  SquareSigma,
  Strikethrough,
  Subscript,
  Superscript,
  Table,
  Underline,
} from 'lucide-vue-next'
import fullEmojiMap from 'markdown-it-emoji/lib/data/full.mjs'
import lightEmojiMap from 'markdown-it-emoji/lib/data/light.mjs'
import emojiShortcutsMap from 'markdown-it-emoji/lib/data/shortcuts.mjs'
import type { Handle } from 'mdast-util-to-markdown'
import type { Component } from 'vue'
import { computed, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Markdown提示块大写类型集合,
  Markdown自定义语法Schema,
} from '../markdown-schema'

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
  scrollSync?: boolean
  showScrollSync?: boolean
}>(), {
  placeholder: '在此编写 Markdown 内容...',
  theme: 'light',
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
const sourceTextareaRef = ref<HTMLTextAreaElement | null>(null)
const editor = ref<Editor | null>(null)
const activeDropdownKey = ref('')
const activeDropdownStyle = ref<Record<string, string>>({})
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
function configureHighlightMarkdownSerializer(ctx: Parameters<MilkdownPlugin>[0]) {
  ctx.update(remarkStringifyOptionsCtx, (options) => ({
    ...options,
    handlers: {
      ...(options.handlers ?? {}),
      break: softLineBreakMarkdownHandler,
      highlight: highlightMarkdownHandler,
    },
  }))
}
const highlightMarkdownPlugins: MilkdownPlugin[] = [
  highlightAttr,
  highlightSchema,
  highlightRemarkPlugin,
  softLineBreakRemarkPlugin,
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
const 代码围栏起始正则 = /^(`{3,}|~{3,})([a-zA-Z0-9_-]*)\s*$/
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

type ToolbarAction =
  | 'heading'
  | 'underline'
  | 'subscript'
  | 'superscript'
  | 'strong'
  | 'emphasis'
  | 'strikethrough'
  | 'highlight'
  | 'link'
  | 'inlineCode'
  | 'blockquote'
  | 'bulletList'
  | 'orderedList'
  | 'taskList'
  | 'codeBlock'
  | 'table'
  | 'hr'
  | 'footnote'
  | 'abbr'
  | 'emojiShortcode'
  | 'image'
  | 'imageLink'
  | 'imageCropUpload'
  | 'mermaid'
  | 'math'
  | 'customMarkdown'
  | 'undo'
  | 'redo'
  | 'format'
  | 'scrollSync'
  | 'pageFullscreen'
  | 'fullscreen'
  | 'sourceMode'

type ToolbarItemType = 'button' | 'dropdown' | 'separator' | 'spacer'

interface ToolbarDropdownOption {
  label: string
  title: string
  action: ToolbarAction
  payload?: string | number
  kind?: 'option'
}

interface ToolbarDropdownDivider {
  label: string
  kind: 'divider'
}

type ToolbarDropdownEntry = ToolbarDropdownOption | ToolbarDropdownDivider

interface ToolbarItem {
  type?: ToolbarItemType
  label: string
  title: string
  action?: ToolbarAction
  payload?: string | number
  icon?: Component
  dynamicIcon?: () => Component
  dropdown?: ToolbarDropdownEntry[]
  hidden?: () => boolean
  disabled?: () => boolean
  active?: () => boolean
}

const 缩写图标 = {
  name: 'AbbreviationIcon',
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 1092 1024',
        xmlns: 'http://www.w3.org/2000/svg',
      },
      [
        h('path', {
          d: 'M937.847467 328.0896l-206.984534-206.984533a55.7056 55.7056 0 0 0-39.389866-16.110934 55.7056 55.7056 0 0 0-39.3216 16.110934L144.384 629.896533a55.7056 55.7056 0 0 0-16.1792 39.389867l2.048 205.960533c0 30.242133 24.1664 54.4768 54.4768 54.4768l205.960533 2.048a55.7056 55.7056 0 0 0 39.3216-16.1792l507.835734-509.7472a55.432533 55.432533 0 0 0 0-77.824zM715.707733 495.616c-2.048 2.048-5.051733 5.051733-8.055466 7.031467l-40.413867 39.389866L546.133333 663.210667 374.510933 836.949333l-150.391466-1.024-1.024-150.391466 341.1968-341.1968 151.415466 151.415466z m127.249067-128.2048l-60.6208 60.552533-152.439467-151.415466 61.576534-61.576534 151.483733 152.439467zM273.066667 273.066667a46.421333 46.421333 0 0 0 65.604266 0L410.282667 201.5232a68.266667 68.266667 0 0 0 0.136533-96.324267L338.602667 32.904533a46.216533 46.216533 0 1 0-65.536 65.536l7.509333 7.509334H47.035733a46.967467 46.967467 0 0 0 0 93.934933H280.576L273.066667 207.394133A46.421333 46.421333 0 0 0 273.066667 273.066667z m772.232533 559.786666H811.690667l7.5776-7.5776a46.421333 46.421333 0 1 0-65.604267-65.604266L681.301333 831.829333a68.266667 68.266667 0 0 0 0.2048 96.733867l71.8848 71.4752a46.557867 46.557867 0 0 0 65.7408-65.7408l-7.509333-7.5776h233.608533a46.967467 46.967467 0 0 0 0-93.866667z',
        }),
      ],
    )
  },
} as Component

const 美化图标 = {
  name: 'FormatMagicIcon',
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 1024 1024',
        xmlns: 'http://www.w3.org/2000/svg',
      },
      [
        h('path', {
          d: 'M951.9 450.2l-98.1-131.5 52.7-155.4c4.4-13 1.1-27.3-8.6-37s-24-13-37-8.6l-155.4 52.7L574 72.3c-11-8.2-25.7-9.4-37.9-3.2s-19.8 18.8-19.7 32.5l2.1 164-133.9 94.7c-11.2 7.9-16.9 21.5-14.8 35 2.1 13.5 11.8 24.7 24.9 28.7l117.8 36.6L74.6 897.8c-14.1 14-14.1 36.8 0 50.9 7 7 16.3 10.6 25.5 10.6s18.4-3.5 25.4-10.5l437.9-437.1L600 629.5c4.1 13.1 15.2 22.7 28.7 24.9 1.9 0.3 3.8 0.4 5.6 0.4 11.6 0 22.6-5.6 29.4-15.2l94.7-133.9 164 2.1c13.7 0.2 26.3-7.4 32.5-19.7 6.5-12.2 5.2-26.9-3-37.9z m-211.4-16.8c-11.8-0.1-23 5.5-29.9 15.2l-63.5 89.8-32.7-105.1c-3.5-11.3-12.4-20.2-23.7-23.7l-105-32.6 89.8-63.5c9.7-6.8 15.4-18 15.2-29.9l-1.4-110 88.2 65.8c9.5 7.1 21.9 9 33.1 5.2l104.2-35.3-35.3 104.2c-3.8 11.2-1.8 23.6 5.2 33.1l65.8 88.2-110-1.4z',
          fill: 'currentColor',
        }),
      ],
    )
  },
} as Component

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

const toolbarItems: ToolbarItem[] = [
  { label: '加粗', title: '加粗', action: 'strong', icon: Bold },
  { label: '下划线', title: '下划线', action: 'underline', icon: Underline },
  { label: '斜体', title: '斜体', action: 'emphasis', icon: Italic },
  { label: '删除线', title: '删除线', action: 'strikethrough', icon: Strikethrough },
  { label: '高亮文本', title: '高亮文本', action: 'highlight', icon: Highlighter },
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
  {
    type: 'dropdown',
    label: '引用',
    title: '引用块',
    action: 'blockquote',
    icon: Quote,
    dropdown: [
      { label: '普通引用块', title: '普通引用块', action: 'blockquote' },
      { label: '常用提示块', kind: 'divider' },
      { label: '说明块', title: '插入 GitHub 风格说明提示块', action: 'customMarkdown', payload: 'github-alert-note' },
      { label: '提示块', title: '插入 GitHub 风格提示提示块', action: 'customMarkdown', payload: 'github-alert-tip' },
      { label: '重要块', title: '插入 GitHub 风格重要提示块', action: 'customMarkdown', payload: 'github-alert-important' },
      { label: '警告块', title: '插入 GitHub 风格警告提示块', action: 'customMarkdown', payload: 'github-alert-warning' },
      { label: '注意块', title: '插入 GitHub 风格注意提示块', action: 'customMarkdown', payload: 'github-alert-caution' },
      { label: '说明', kind: 'divider' },
      { label: '查看提示块语法', title: '查看全部提示块语法', action: 'customMarkdown', payload: 'github-alert-syntax' },
    ],
  },
  { label: '无序列表', title: '无序列表', action: 'bulletList', icon: List },
  { label: '有序列表', title: '有序列表', action: 'orderedList', icon: ListOrdered },
  { label: '任务列表', title: '任务列表', action: 'taskList', icon: ListTodo },
  { label: '分割线', title: '分割线', action: 'hr', icon: SeparatorHorizontal },
  { type: 'separator', label: '', title: '' },
  { label: '行内代码', title: '行内代码', action: 'inlineCode', icon: Code },
  {
    type: 'dropdown',
    label: '块级代码',
    title: '增强代码块',
    action: 'codeBlock',
    icon: SquareCode,
    dropdown: [
      { label: '默认代码块', title: '插入默认代码块', action: 'codeBlock' },
      { label: '说明', kind: 'divider' },
      { label: '查看代码块语法', title: '查看增强代码块语法', action: 'customMarkdown', payload: 'code-syntax' },
    ],
  },
  { label: '超链接', title: '超链接', action: 'link', icon: Link },
  { label: '脚注', title: '脚注', action: 'footnote', icon: Pilcrow },
  { label: '缩写', title: '缩写', action: 'abbr', icon: 缩写图标 },
  { type: 'dropdown', label: 'Emoji 短码', title: 'Emoji 短码', action: 'emojiShortcode', icon: Smile },
  {
    type: 'dropdown',
    label: '图片',
    title: '图片',
    action: 'image',
    icon: Image,
    dropdown: [
      { label: '上传图片', title: '上传图片', action: 'image' },
      { label: '添加图片链接', title: '添加图片链接', action: 'imageLink' },
      { label: '裁剪上传', title: '裁剪上传', action: 'imageCropUpload' },
      { label: '图片网络', title: '插入图片网络', action: 'customMarkdown', payload: 'image-grid' },
    ],
    disabled: () => isUploading.value,
  },
  {
    type: 'dropdown',
    label: '其他块',
    title: '其他自定义块',
    action: 'customMarkdown',
    icon: Blocks,
    dropdown: [
      { label: '容器式提示块', title: '插入 :::type[title] 提示块', action: 'customMarkdown', payload: 'container-alert' },
      { label: '缩进式提示块', title: '插入 !!! type 提示块', action: 'customMarkdown', payload: 'indented-alert' },
      { label: '折叠块（已折叠）', title: '插入默认收起的 ??? type 折叠块', action: 'customMarkdown', payload: 'details-alert-collapsed' },
      { label: '折叠块（未折叠）', title: '插入默认展开的 ???+ type 折叠块', action: 'customMarkdown', payload: 'details-alert-expanded' },
    ],
  },
  { label: '标签页', title: '标签页', action: 'customMarkdown', payload: 'tabs', icon: LayoutPanelTop },
  { label: 'GitHub 仓库卡片', title: 'GitHub 仓库卡片', action: 'customMarkdown', payload: 'github-card', icon: Github },
  { label: '剧透文本', title: '剧透文本', action: 'customMarkdown', payload: 'spoiler', icon: EyeOff },
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
  { label: '美化', title: '美化', action: 'format', icon: 美化图标, hidden: () => !props.formatContent },
  {
    label: '同步滚动',
    title: '同步滚动',
    action: 'scrollSync',
    icon: ArrowDownUp,
    hidden: () => !props.showScrollSync,
    active: () => props.scrollSync,
  },
  {
    label: '源码',
    title: '源码和显示模式切换',
    action: 'sourceMode',
    dynamicIcon: () => (isSourceMode.value ? FilePenLine : FileCode),
    active: () => isSourceMode.value,
  },
  { label: '浏览器全屏', title: '浏览器全屏', action: 'pageFullscreen', icon: Maximize2 },
  { label: '屏幕全屏', title: '屏幕全屏', action: 'fullscreen', icon: Expand },
]

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
  await createEditor()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
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
        if (event.isComposing || event.shiftKey || event.altKey) {
          return false
        }

        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
          event.preventDefault()
          return insertSoftLineBreak(view)
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
    language: codeFenceMatch[2] ?? '',
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
      configureHighlightMarkdownSerializer(ctx)
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
    .replace(转义剧透文本正则, `:${剧透语法名称}[$1]`)
    .replace(转义GitHub卡片正则, `::${GitHub卡片语法名称}{repo="$1"}`)
    .replace(
      转义Emoji短码正则,
      (_match, shortcode: string) => `:${shortcode.replace(/\\_/g, '_')}:`,
    )

  return normalizeSerializedMarkdownBlocks(normalizeSerializedMarkdownMarkers(normalizedMarkdown))
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
    emit('update:scrollSync', !props.scrollSync)
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
                :is="getToolbarIcon(item)"
                v-if="getToolbarIcon(item)"
                class="milkdown-markdown-editor__toolbar-icon"
                aria-hidden="true"
              />
            </button>
            <div
              v-if="activeDropdownKey === getToolbarItemKey(item, itemIndex)"
              class="milkdown-markdown-editor__toolbar-menu"
              :class="{
                'milkdown-markdown-editor__toolbar-menu--table': item.action === 'table',
                'milkdown-markdown-editor__toolbar-menu--emoji': item.action === 'emojiShortcode',
              }"
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
                <button
                  class="milkdown-markdown-editor__toolbar-menu-item milkdown-markdown-editor__table-more-button"
                  type="button"
                  title="插入更多表格"
                  @click="openTableDialog"
                >
                  更多表格
                </button>
              </template>
              <template v-else-if="item.action === 'emojiShortcode'">
                <template v-if="emojiPickerMode === 'emoji' && 常用Emoji选项.length > 0">
                  <div class="milkdown-markdown-editor__emoji-section-title">
                    常用 Emoji
                  </div>
                  <div class="milkdown-markdown-editor__emoji-common-grid">
                    <button
                      v-for="option in 常用Emoji选项"
                      :key="`common-${option.shortcode}`"
                      class="milkdown-markdown-editor__emoji-button"
                      type="button"
                      :title="`:${option.shortcode}:`"
                      @click="insertEmojiShortcode(option.shortcode)"
                    >
                      <span class="milkdown-markdown-editor__emoji-symbol">{{ option.emoji }}</span>
                    </button>
                  </div>
                  <div class="milkdown-markdown-editor__emoji-divider" />
                </template>
                <template v-else-if="emojiPickerMode === 'kaomoji' && 常用颜文字选项.length > 0">
                  <div class="milkdown-markdown-editor__emoji-section-title">
                    常用颜文字
                  </div>
                  <div class="milkdown-markdown-editor__kaomoji-common-grid">
                    <button
                      v-for="option in 常用颜文字选项"
                      :key="`common-kaomoji-${option.shortcut}`"
                      class="milkdown-markdown-editor__kaomoji-button"
                      type="button"
                      :title="option.shortcode ? `${option.shortcut} -> :${option.shortcode}:` : option.shortcut"
                      @click="insertKaomoji(option.shortcut)"
                    >
                      {{ option.shortcut }}
                    </button>
                  </div>
                  <div class="milkdown-markdown-editor__emoji-divider" />
                </template>
                <div
                  v-if="emojiPickerMode === 'emoji'"
                  class="milkdown-markdown-editor__emoji-scroll-grid"
                >
                  <button
                    v-for="option in 轻量Emoji选项"
                    :key="`light-${option.shortcode}`"
                    class="milkdown-markdown-editor__emoji-button"
                    type="button"
                    :title="`:${option.shortcode}:`"
                    @click="insertEmojiShortcode(option.shortcode)"
                  >
                    <span class="milkdown-markdown-editor__emoji-symbol">{{ option.emoji }}</span>
                  </button>
                </div>
                <div
                  v-else
                  class="milkdown-markdown-editor__kaomoji-scroll-list"
                >
                  <button
                    v-for="option in 颜文字选项"
                    :key="`kaomoji-${option.shortcode}-${option.shortcut}`"
                    class="milkdown-markdown-editor__kaomoji-row"
                    type="button"
                    :title="option.shortcode ? `${option.shortcut} -> :${option.shortcode}:` : option.shortcut"
                    @click="insertKaomoji(option.shortcut)"
                  >
                    <span>{{ option.shortcut }}</span>
                    <span v-if="option.emoji" class="milkdown-markdown-editor__kaomoji-emoji">{{ option.emoji }}</span>
                  </button>
                </div>
                <div class="milkdown-markdown-editor__emoji-footer">
                  <button
                    class="milkdown-markdown-editor__emoji-footer-button"
                    type="button"
                    :class="{ 'is-active': emojiPickerMode === 'emoji' }"
                    @click="emojiPickerMode = 'emoji'"
                  >
                    Emoji
                  </button>
                  <button
                    class="milkdown-markdown-editor__emoji-footer-button"
                    type="button"
                    :class="{ 'is-active': emojiPickerMode === 'kaomoji' }"
                    @click="emojiPickerMode = 'kaomoji'"
                  >
                    颜文字
                  </button>
                  <button
                    class="milkdown-markdown-editor__emoji-footer-button"
                    type="button"
                    @click="openEmojiDialog"
                  >
                    更多
                  </button>
                </div>
              </template>
              <template v-else>
                <template v-for="option in item.dropdown" :key="`${option.kind ?? 'option'}-${option.label}-${option.kind === 'option' ? option.payload ?? option.action : ''}`">
                  <div
                    v-if="option.kind === 'divider'"
                    class="milkdown-markdown-editor__toolbar-menu-divider"
                  >
                    {{ option.label }}
                  </div>
                  <button
                    v-else
                    class="milkdown-markdown-editor__toolbar-menu-item"
                    type="button"
                    :title="option.title"
                    @click="runToolbarAction(option.action, option.payload); closeToolbarDropdown()"
                  >
                    {{ option.label }}
                  </button>
                </template>
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
            @click="item.action && runToolbarAction(item.action, item.payload)"
          >
            <component
              :is="getToolbarIcon(item)"
              v-if="getToolbarIcon(item)"
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
      <input
        ref="cropFileInputRef"
        class="milkdown-markdown-editor__file-input"
        type="file"
        accept="image/*"
        @change="handleCropFileInputChange"
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
  width: max-content;
  min-width: 0;
}

.milkdown-markdown-editor__toolbar-menu--emoji {
  width: 240px;
}

.milkdown-markdown-editor__toolbar-menu-divider {
  display: flex;
  align-items: center;
  min-height: 24px;
  padding: 6px 10px 2px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

.milkdown-markdown-editor__toolbar-menu-divider:not(:first-child) {
  margin-top: 4px;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
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
  gap: 3px;
}

.milkdown-markdown-editor__table-size-row {
  display: grid;
  grid-template-columns: repeat(6, 16px);
  gap: 3px;
  padding: 0;
  border: none;
  background: transparent;
}

.milkdown-markdown-editor__table-size-cell {
  width: 16px;
  height: 16px;
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

.milkdown-markdown-editor__table-more-button {
  position: relative;
  justify-content: center;
  margin-top: 6px;
  padding-top: 5px;
  background: transparent;
  text-align: center;
}

.milkdown-markdown-editor__table-more-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__table-more-button::after {
  content: '';
  position: absolute;
  inset: 5px 0 0;
  z-index: -1;
  border-radius: 4px;
  background: color-mix(in srgb, var(--el-color-primary) 5%, transparent);
}

.milkdown-markdown-editor__table-more-button:hover,
.milkdown-markdown-editor__table-more-button:focus-visible {
  background: transparent;
}

.milkdown-markdown-editor__table-more-button:hover::after,
.milkdown-markdown-editor__table-more-button:focus-visible::after {
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
}

.milkdown-markdown-editor__emoji-section-title {
  display: flex;
  align-items: center;
  min-height: 22px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
}

.milkdown-markdown-editor__emoji-common-grid,
.milkdown-markdown-editor__emoji-scroll-grid {
  display: grid;
  grid-template-columns: repeat(8, 24px);
  gap: 3px;
}

.milkdown-markdown-editor__emoji-scroll-grid {
  max-height: 150px;
  overflow: auto;
  padding-right: 2px;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__emoji-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-editor__emoji-button:hover,
.milkdown-markdown-editor__emoji-button:focus-visible,
.milkdown-markdown-editor__kaomoji-button:hover,
.milkdown-markdown-editor__kaomoji-button:focus-visible,
.milkdown-markdown-editor__kaomoji-row:hover,
.milkdown-markdown-editor__kaomoji-row:focus-visible {
  outline: none;
  background: color-mix(in srgb, var(--el-color-primary) 10%, transparent);
  color: var(--el-color-primary);
}

.milkdown-markdown-editor__emoji-symbol {
  font-size: 18px;
  line-height: 1;
}

.milkdown-markdown-editor__kaomoji-common-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
}

.milkdown-markdown-editor__kaomoji-button,
.milkdown-markdown-editor__kaomoji-row {
  min-height: 26px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--el-text-color-primary);
  font: 13px/1.2 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
  cursor: pointer;
}

.milkdown-markdown-editor__kaomoji-button {
  padding: 0 7px;
  text-align: center;
}

.milkdown-markdown-editor__kaomoji-scroll-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2px;
  max-height: 150px;
  overflow: auto;
  padding-right: 2px;
  scrollbar-width: thin;
}

.milkdown-markdown-editor__kaomoji-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  width: 100%;
  padding: 0 8px;
  text-align: left;
}

.milkdown-markdown-editor__kaomoji-emoji {
  flex: 0 0 auto;
  font-size: 16px;
}

.milkdown-markdown-editor__emoji-divider {
  margin: 6px 0;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__emoji-footer {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid color-mix(in srgb, var(--el-border-color) 70%, transparent);
}

.milkdown-markdown-editor__emoji-footer-button {
  min-height: 26px;
  padding: 0 6px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 12px;
  cursor: pointer;
}

.milkdown-markdown-editor__emoji-footer-button:hover,
.milkdown-markdown-editor__emoji-footer-button:focus-visible,
.milkdown-markdown-editor__emoji-footer-button.is-active {
  border-color: var(--el-color-primary);
  outline: none;
  color: var(--el-color-primary);
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

.milkdown-markdown-editor :deep(.ProseMirror mark) {
  border-radius: 4px;
  padding: 1px 5px;
  background: color-mix(in srgb, var(--el-color-warning) 28%, var(--el-bg-color));
  color: var(--el-text-color-primary);
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
  cursor: pointer;
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
