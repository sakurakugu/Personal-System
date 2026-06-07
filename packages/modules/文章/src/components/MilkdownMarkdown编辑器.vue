<script setup lang="ts">
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
import { insertTableCommand } from '@milkdown/preset-gfm'
import { redo } from '@milkdown/prose/history'
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
const isEditorReadyForLocalUpdates = ref(false)
const isMilkdownContentPristine = ref(true)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
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

  isMilkdownContentPristine.value = false
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
  background: var(--milkdown-markdown-editor-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-bg-color, var(--el-bg-color-overlay));
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
  background: var(--milkdown-markdown-editor-toolbar-bg, var(--el-bg-color-overlay));
  background-color: var(--milkdown-markdown-editor-toolbar-bg-color, var(--el-bg-color-overlay));
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
