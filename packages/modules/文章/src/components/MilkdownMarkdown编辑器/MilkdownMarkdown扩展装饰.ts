import type { Node as ProseNode } from '@milkdown/prose/model'
import { Decoration, DecorationSet } from '@milkdown/prose/view'
import { Markdown提示块大写类型集合 } from '../../markdown-schema'
import {
  Emoji短码正则,
  GitHub卡片正则,
  GitHub提示块正则,
  剧透文本正则,
  剧透语法名称,
  缩写定义正则,
  行内数学正则,
  转义块级数学围栏正则,
} from './MilkdownMarkdown语法常量'

type MarkdownTextBlock = {
  node: ProseNode
  pos: number
  from: number
  to: number
  text: string
}

export function buildExtendedMarkdownDecorations(doc: ProseNode): DecorationSet {
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
