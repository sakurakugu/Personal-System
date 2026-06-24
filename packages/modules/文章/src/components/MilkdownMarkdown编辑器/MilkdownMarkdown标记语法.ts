import { remarkStringifyOptionsCtx } from '@milkdown/core'
import type { MilkdownPlugin } from '@milkdown/ctx'
import { markRule } from '@milkdown/prose'
import type { MarkdownNode } from '@milkdown/transformer'
import { $inputRule, $markAttr, $markSchema, $remark } from '@milkdown/utils'
import type { Handle } from 'mdast-util-to-markdown'
import { 清理代码块信息文本 } from './MilkdownMarkdown语法常量'

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

export function configureMarkdownSerializer(ctx: Parameters<MilkdownPlugin>[0]) {
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

export const highlightMarkdownPlugins: MilkdownPlugin[] = [
  highlightAttr,
  highlightSchema,
  highlightRemarkPlugin,
  softLineBreakRemarkPlugin,
  codeFenceInfoRemarkPlugin,
  highlightInputRule,
].flat()

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
