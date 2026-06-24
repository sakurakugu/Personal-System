import type { ToolbarAction } from '../MilkdownMarkdown工具栏/MilkdownMarkdown工具栏类型'
import { buildMermaidSnippet } from './Markdown自定义语法片段'

export const 表格行列选项 = [1, 2, 3, 4, 5, 6]
export const 更多表格最大行列 = 20
export const 表格基础语法说明 = [
  '| 左对齐 | 居中对齐 | 右对齐 | 默认 |',
  '| :-- | :--: | --: | --- |',
  '| 内容 | 内容 | 内容 | 内容 |',
  '',
  ':-- 表示左对齐',
  ':--: 表示居中对齐',
  '--: 表示右对齐',
  '--- 表示正常的标题和内容的分隔线',
].join('\n')

export function normalizeHeadingLevel(payload?: string | number): 1 | 2 | 3 | 4 | 5 | 6 {
  const level = Number(payload ?? 1)
  if (level >= 1 && level <= 6) {
    return level as 1 | 2 | 3 | 4 | 5 | 6
  }

  return 1
}

export function normalizeTableSizePayload(payload?: string | number): { row: number; col: number } {
  if (typeof payload === 'string') {
    const [row, col] = payload.split('x').map((item) => Number(item))
    return {
      row: normalizeTableSize(row, 3),
      col: normalizeTableSize(col, 3),
    }
  }

  return { row: 3, col: 3 }
}

export function normalizeCustomTableSize(value: number, fallback: number): number {
  if (!Number.isInteger(value)) {
    return fallback
  }

  return Math.min(更多表格最大行列, Math.max(1, value))
}

export function buildTableMarkdown(size: { row: number; col: number }): string {
  const header = `| ${Array.from({ length: size.col }, (_, index) => `列 ${index + 1}`).join(' | ')} |`
  const separator = `| ${Array.from({ length: size.col }, () => '---').join(' | ')} |`
  const bodyRows = Array.from(
    { length: Math.max(1, size.row - 1) },
    () => `| ${Array.from({ length: size.col }, () => '').join(' | ')} |`,
  )
  return `\n${[header, separator, ...bodyRows].join('\n')}\n`
}

export function shouldInsertMarkdownSnippet(action: ToolbarAction): boolean {
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

export function buildToolbarMarkdownSnippet(action: ToolbarAction, payload?: string | number): string {
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

function normalizeTableSize(value: number, fallback: number): number {
  if (!Number.isInteger(value)) {
    return fallback
  }

  return Math.min(6, Math.max(1, value))
}
