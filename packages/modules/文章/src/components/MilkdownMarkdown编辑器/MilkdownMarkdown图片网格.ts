import type { MilkdownPlugin } from '@milkdown/ctx'
import { remarkStringifyOptionsCtx } from '@milkdown/core'
import type { Node as ProseNode } from '@milkdown/prose/model'
import { Plugin } from '@milkdown/prose/state'
import type { MarkdownNode } from '@milkdown/transformer'
import { $nodeSchema, $prose, $remark } from '@milkdown/utils'
import type { Handle } from 'mdast-util-to-markdown'
import { Markdown自定义语法Schema } from '../../markdown-schema'

declare module 'mdast-util-to-markdown' {
  interface ConstructNameMap {
    imageGrid: 'imageGrid'
  }
}

type 可变Markdown节点 = MarkdownNode & {
  type: string
  children?: 可变Markdown节点[]
  value?: unknown
}

const 图片网格节点类型 = 'imageGrid'
const 图片网格开始标记 = Markdown自定义语法Schema.imageGrid.openMarker
const 图片网格结束标记 = Markdown自定义语法Schema.imageGrid.closeMarker

const imageGridMarkdownHandler: Handle = (node, _parent, state, info) => {
  const tracker = state.createTracker(info)
  const gridNode = node as 可变Markdown节点
  const flowNode = {
    type: 'root',
    children: gridNode.children ?? [],
  } as Parameters<typeof state.containerFlow>[0]
  const content = state.containerFlow(flowNode, tracker.current()).trim()

  if (!content) {
    return `${图片网格开始标记}\n${图片网格结束标记}`
  }

  return `${图片网格开始标记}\n${content}\n${图片网格结束标记}`
}

const imageGridSchema = $nodeSchema(图片网格节点类型, () => ({
  content: 'block+',
  group: 'block',
  defining: true,
  isolating: true,
  parseDOM: [{ tag: 'div[data-milkdown-node="image-grid"]' }],
  toDOM: () => [
    'div',
    {
      class: 'milkdown-image-grid',
      'data-milkdown-node': 'image-grid',
    },
    ['div', { class: 'milkdown-image-grid__content' }, 0],
  ],
  parseMarkdown: {
    match: (node) => node.type === 图片网格节点类型,
    runner: (state, node, type) => {
      state.openNode(type).next(node.children).closeNode()
    },
  },
  toMarkdown: {
    match: (node: ProseNode) => node.type.name === 图片网格节点类型,
    runner: (state, node) => {
      state.openNode(图片网格节点类型).next(node.content).closeNode()
    },
  },
}))

const imageGridRemarkPlugin = $remark('imageGridMarkdown', () => () => (tree) => {
  transformImageGridMarkdownNodes(tree as 可变Markdown节点)
})

const imageGridCleanupPlugin = $prose(() => new Plugin({
  appendTransaction(transactions, _oldState, newState) {
    if (!transactions.some((transaction) => transaction.docChanged)) {
      return null
    }

    const 删除范围列表: Array<{ from: number, to: number }> = []

    newState.doc.descendants((node, pos) => {
      if (node.type.name !== 图片网格节点类型) {
        return true
      }

      let childPos = pos + 1
      const 空图片网格项范围列表: Array<{ from: number, to: number }> = []
      node.forEach((child) => {
        if (是否空图片网格项(child)) {
          空图片网格项范围列表.push({
            from: childPos,
            to: childPos + child.nodeSize,
          })
        }

        childPos += child.nodeSize
      })

      if (空图片网格项范围列表.length > 0 && 空图片网格项范围列表.length < node.childCount) {
        删除范围列表.push(...空图片网格项范围列表)
      }

      return false
    })

    if (删除范围列表.length === 0) {
      return null
    }

    const tr = newState.tr
    删除范围列表
      .sort((left, right) => right.from - left.from)
      .forEach((range) => tr.delete(range.from, range.to))

    return tr
  },
}))

export function configureImageGridMarkdownSerializer(ctx: Parameters<MilkdownPlugin>[0]) {
  ctx.update(remarkStringifyOptionsCtx, (options) => ({
    ...options,
    handlers: {
      ...(options.handlers ?? {}),
      imageGrid: imageGridMarkdownHandler,
    },
  }))
}

export const imageGridMarkdownPlugins: MilkdownPlugin[] = [
  imageGridSchema,
  imageGridRemarkPlugin,
  imageGridCleanupPlugin,
].flat()

function 是否空图片网格项(node: ProseNode): boolean {
  if (node.type.name !== 'paragraph') {
    return false
  }

  if (node.childCount === 0) {
    return true
  }

  let 仅包含换行占位 = true
  node.forEach((child) => {
    if (!是否换行占位节点(child)) {
      仅包含换行占位 = false
    }
  })

  return 仅包含换行占位
}

function 是否换行占位节点(node: ProseNode): boolean {
  if (node.isText) {
    return node.textContent.trim().length === 0
  }

  if (node.type.name === 'hardbreak') {
    return true
  }

  return node.type.name === 'html' && ['<br />', '<br>', '<br >', '<br/>'].includes(String(node.attrs.value).trim())
}

function transformImageGridMarkdownNodes(node: 可变Markdown节点): void {
  if (Array.isArray(node.children)) {
    node.children = groupImageGridChildren(expandInlineImageGridMarkers(node.children))
    node.children.forEach((child) => transformImageGridMarkdownNodes(child))
  }
}

function expandInlineImageGridMarkers(children: 可变Markdown节点[]): 可变Markdown节点[] {
  return children.flatMap((child) => {
    if (child.type !== 'paragraph' || !Array.isArray(child.children)) {
      return [child]
    }

    return 拆分段落图片网格标记(child)
  })
}

function 拆分段落图片网格标记(paragraph: 可变Markdown节点): 可变Markdown节点[] {
  const children = paragraph.children ?? []
  if (!children.some((child) => child.type === 'text' && typeof child.value === 'string' && 包含图片网格标记(child.value))) {
    return [paragraph]
  }

  const result: 可变Markdown节点[] = []
  let inlineChildren: 可变Markdown节点[] = []

  const pushInlineParagraph = () => {
    if (inlineChildren.length === 0 || inlineChildren.every(是否空白文本节点)) {
      inlineChildren = []
      return
    }

    result.push({
      type: 'paragraph',
      children: inlineChildren,
    })
    inlineChildren = []
  }

  for (const child of children) {
    if (child.type !== 'text' || typeof child.value !== 'string' || !包含图片网格标记(child.value)) {
      inlineChildren.push(child)
      continue
    }

    拆分文本图片网格标记(child.value, (item) => {
      if (item.type === 'text') {
        inlineChildren.push({
          type: 'text',
          value: item.value,
        })
        return
      }

      pushInlineParagraph()
      result.push(创建网格标记段落(item.value))
    })
  }

  pushInlineParagraph()
  return result.length > 0 ? result : [paragraph]
}

function 拆分文本图片网格标记(
  text: string,
  visit: (item: { type: 'text' | 'marker', value: string }) => void,
) {
  let rest = text

  while (rest.length > 0) {
    const nextMarker = 查找下一个图片网格标记(rest)
    if (!nextMarker) {
      visit({ type: 'text', value: rest })
      return
    }

    if (nextMarker.index > 0) {
      visit({ type: 'text', value: rest.slice(0, nextMarker.index) })
    }

    visit({ type: 'marker', value: nextMarker.marker })
    rest = rest.slice(nextMarker.index + nextMarker.marker.length)
  }
}

function 查找下一个图片网格标记(text: string): { index: number, marker: string } | null {
  const openIndex = text.indexOf(图片网格开始标记)
  const closeIndex = text.indexOf(图片网格结束标记)

  if (openIndex === -1 && closeIndex === -1) {
    return null
  }

  if (openIndex !== -1 && (closeIndex === -1 || openIndex < closeIndex)) {
    return {
      index: openIndex,
      marker: 图片网格开始标记,
    }
  }

  return {
    index: closeIndex,
    marker: 图片网格结束标记,
  }
}

function 包含图片网格标记(text: string): boolean {
  return text.includes(图片网格开始标记) || text.includes(图片网格结束标记)
}

function groupImageGridChildren(children: 可变Markdown节点[]): 可变Markdown节点[] {
  const groupedChildren: 可变Markdown节点[] = []
  let gridChildren: 可变Markdown节点[] | null = null

  for (const child of children) {
    const marker = 读取图片网格标记(child)

    if (marker === 'open') {
      if (gridChildren) {
        groupedChildren.push(创建图片网格节点(gridChildren))
      }
      gridChildren = []
      continue
    }

    if (marker === 'close') {
      if (gridChildren) {
        groupedChildren.push(创建图片网格节点(gridChildren))
        gridChildren = null
        continue
      }

      groupedChildren.push(child)
      continue
    }

    if (gridChildren) {
      gridChildren.push(child)
    } else {
      groupedChildren.push(child)
    }
  }

  if (gridChildren) {
    groupedChildren.push(创建网格标记段落(图片网格开始标记), ...gridChildren)
  }

  return groupedChildren
}

function 读取图片网格标记(node: 可变Markdown节点): 'open' | 'close' | null {
  if (node.type !== 'paragraph' || node.children?.length !== 1) {
    return null
  }

  const [child] = node.children
  if (child?.type !== 'text' || typeof child.value !== 'string') {
    return null
  }

  const value = child.value.trim()
  if (value === 图片网格开始标记) {
    return 'open'
  }
  if (value === 图片网格结束标记) {
    return 'close'
  }

  return null
}

function 创建图片网格节点(children: 可变Markdown节点[]): 可变Markdown节点 {
  return {
    type: 图片网格节点类型,
    children: children.length > 0 ? 规范化图片网格子节点(children) : [创建空段落()],
  }
}

function 规范化图片网格子节点(children: 可变Markdown节点[]): 可变Markdown节点[] {
  return children.flatMap((child) => {
    if (child.type !== 'paragraph' || !Array.isArray(child.children)) {
      return [child]
    }

    const imageChildren = child.children.filter((item) => item.type === 'image')
    if (
      imageChildren.length <= 1
      || child.children.some((item) => item.type !== 'image' && !是否空白文本节点(item))
    ) {
      return [child]
    }

    return imageChildren.map((image) => ({
      type: 'paragraph',
      children: [image],
    }))
  })
}

function 是否空白文本节点(node: 可变Markdown节点): boolean {
  return node.type === 'text' && typeof node.value === 'string' && node.value.trim().length === 0
}

function 创建网格标记段落(marker: string): 可变Markdown节点 {
  return {
    type: 'paragraph',
    children: [
      {
        type: 'text',
        value: marker,
      },
    ],
  }
}

function 创建空段落(): 可变Markdown节点 {
  return {
    type: 'paragraph',
    children: [],
  }
}
