import type { Node as ProseNode } from '@milkdown/prose/model'
import { setBlockType } from '@milkdown/prose/commands'
import { liftListItem } from '@milkdown/prose/schema-list'
import { Plugin, TextSelection } from '@milkdown/prose/state'
import type { EditorView } from '@milkdown/prose/view'
import type { Parser } from '@milkdown/transformer'
import {
  代码围栏起始正则,
  清理代码块信息文本,
  表格简写正则,
} from './MilkdownMarkdown语法常量'

interface MarkdownKeyboardPluginOptions {
  toggleStrong?: (view: EditorView) => boolean
  toggleHeading?: (view: EditorView, level: MarkdownHeadingLevel) => boolean
}

export type MarkdownHeadingLevel = 1 | 2 | 3 | 4 | 5 | 6

export function createMarkdownKeyboardPlugin(
  parser: Parser,
  listItemType: ProseNode['type'],
  options: MarkdownKeyboardPluginOptions = {},
) {
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

        if (isMarkdownStrongShortcut(event)) {
          event.preventDefault()
          return options.toggleStrong?.(view) ?? false
        }

        const headingLevel = getMarkdownHeadingShortcutLevel(event)
        if (headingLevel) {
          event.preventDefault()
          return options.toggleHeading?.(view, headingLevel) ?? toggleHeading(view, headingLevel)
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

export function isMarkdownStrongShortcut(event: KeyboardEvent): boolean {
  return !event.isComposing
    && !event.altKey
    && !event.shiftKey
    && (event.ctrlKey || event.metaKey)
    && event.key.toLowerCase() === 'b'
}

export function getMarkdownHeadingShortcutLevel(event: KeyboardEvent): MarkdownHeadingLevel | null {
  if (
    event.isComposing
    || event.altKey
    || event.shiftKey
    || !(event.ctrlKey || event.metaKey)
  ) {
    return null
  }

  const level = Number(event.key)
  if (Number.isInteger(level) && level >= 1 && level <= 6) {
    return level as MarkdownHeadingLevel
  }

  return null
}

function toggleHeading(view: EditorView, level: MarkdownHeadingLevel): boolean {
  const { state } = view
  const headingType = state.schema.nodes.heading
  const paragraphType = state.schema.nodes.paragraph
  if (!headingType || !paragraphType) {
    return false
  }

  if (isSelectedHeadingLevel(view, level)) {
    return setBlockType(paragraphType)(state, view.dispatch, view)
  }

  return setBlockType(headingType, { level })(state, view.dispatch, view)
}

function isSelectedHeadingLevel(view: EditorView, level: MarkdownHeadingLevel): boolean {
  const { state } = view
  const { selection } = state

  if (selection.empty) {
    const node = selection.$from.parent
    return node.type.name === 'heading' && Number(node.attrs.level) === level
  }

  let foundTextBlock = false
  let allTextBlocksAreTargetHeading = true
  state.doc.nodesBetween(selection.from, selection.to, (node) => {
    if (!node.isTextblock) {
      return true
    }

    foundTextBlock = true
    if (node.type.name !== 'heading' || Number(node.attrs.level) !== level) {
      allTextBlocksAreTargetHeading = false
    }
    return false
  })

  return foundTextBlock && allTextBlocksAreTargetHeading
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
