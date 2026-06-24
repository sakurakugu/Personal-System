import { Markdown自定义语法Schema } from '../../markdown-schema'

export const 标签页标题内容正则源码 = '(?:[^"\\\\]|\\\\.)+'
export const Markdown类型名正则源码 = '[A-Za-z][\\w-]*'
export const 剧透语法名称 = Markdown自定义语法Schema.spoiler.pattern.match(/^:([a-zA-Z][\w-]*)/)?.[1] ?? 'spoiler'
export const GitHub卡片语法名称 = Markdown自定义语法Schema.githubCard.pattern.match(/^::([a-zA-Z][\w-]*)/)?.[1] ?? 'github'

const 图片网格开始标记 = 转义正则文本(Markdown自定义语法Schema.imageGrid.openMarker.slice(1, -1))
const 图片网格结束标记 = 转义正则文本(Markdown自定义语法Schema.imageGrid.closeMarker.slice(1, -1))
const 剧透语法名正则源码 = 转义正则文本(剧透语法名称)
const GitHub卡片语法名正则源码 = 转义正则文本(GitHub卡片语法名称)

export const 表格简写正则 = /^\|(.+)\|\s*$/
export const 代码围栏起始正则 = /^(`{3,}|~{3,})([^\r\n`]*)$/
export const 标签页标题转义正则 = new RegExp(`^\\\\(===\\s+"${标签页标题内容正则源码}"\\s*)$`, 'gm')
export const 标签页压缩代码块正则 = new RegExp(
  `^\\\\===\\s+"(${标签页标题内容正则源码})"\\s*\\n\`([a-zA-Z0-9_-]+)\\s+([^\`\\n]+)\``,
  'gm',
)
export const 缩写定义正则 = /^\\?\*\\?\[([^\]\\\n]+)\?]:(\s+.+)$/gm
export const 扩展块标题正则 = new RegExp(`^(\\s*)(!!!|\\?\\?\\?\\+?)\\s+${Markdown类型名正则源码}(?:\\s+.*)?$`)
export const 标签页标题正则 = new RegExp(`^(\\s*)===\\s+"${标签页标题内容正则源码}"\\s*$`)
export const 容器提示块标题正则 = new RegExp(
  `^(\\s*):::${Markdown类型名正则源码}(?:\\\\?\\[(?:[^\\]\\\\]|\\\\.)*\\\\?])?\\s*$`,
)
export const 容器提示块结束正则 = /^\s*:::\s*$/
export const 扩展块标题转义正则 = /^(\s*)\\(!!!|\?\?\?\+?|===)(.*)$/
export const 容器提示块标题转义正则 = /^(\s*)\\:::(.*)$/
export const 容器提示块标题方括号转义正则 = /\\([\][])/g
export const 图片网格标记转义正则 = new RegExp(`\\\\\\[(${图片网格开始标记}|${图片网格结束标记})\\\\?]`, 'gi')
export const GitHub提示块正则 = new RegExp(`^(?:>\\s*)?\\\\?\\[!(${Markdown类型名正则源码})](.*)$`, 'gm')
export const 转义GitHub提示块正文正则 = new RegExp(`\\\\\\[!(${Markdown类型名正则源码})]`, 'g')
export const 转义缩写定义正则 = /^\\\*\?\[([^\]\\\n]+)\?]:(\s+.+)$/gm
export const 转义Emoji短码正则 = /\\?:((?:[a-zA-Z0-9_+-]|\\_)+)\\?:/g
export const 转义剧透文本正则 = new RegExp(`\\\\?:${剧透语法名正则源码}\\\\?\\[((?:[^\\]\\\\]|\\\\.)*)\\\\?]`, 'g')
export const 转义GitHub卡片正则 = new RegExp(
  `\\\\?:\\\\?:${GitHub卡片语法名正则源码}\\\\?\\{repo=\\\\?"([^"\\\\]+\\/[^"\\\\]+)\\\\?"\\\\?}`,
  'g',
)
export const 转义块级数学围栏正则 = /^\\\$\\\$\s*$/
export const 转义块级数学围栏全局正则 = /^\\\$\\\$\s*$/gm
export const 转义行内数学正则 = /(^|[^\\])\\\$([^$\n]+?)\\\$/g
export const 转义图片语法正则 = /\\?!\?\[((?:\\.|[^\]\\])*)\?\]\\?\(((?:\\.|[^)\\])*)\?\)/g
export const 代码围栏边界正则 = /^(\s*)(`{3,}|~{3,})/
export const 转义代码围栏边界正则 = /^(\s*)\\(`{3,}|~{3,})/
export const 星号水平线正则 = /^\s*\*(?:\s+\*){2,}\s*$/
export const 星号紧凑水平线正则 = /^\s*\*{3,}\s*$/
export const Emoji短码正则 = /:([a-zA-Z0-9_+-]+):/g
export const 剧透文本正则 = new RegExp(`\\\\?:${剧透语法名正则源码}\\\\?\\[((?:[^\\]\\\\]|\\\\.)*)\\\\?]`, 'g')
export const 行内数学正则 = /(^|[^\\])\$([^$\n]+?)\$/g
export const GitHub卡片正则 = new RegExp(
  `\\\\?:\\\\?:${GitHub卡片语法名正则源码}\\\\?\\{repo=\\\\?"([^"\\\\]+\\/[^"\\\\]+)\\\\?"\\\\?}`,
  'g',
)

export function 转义正则文本(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function 清理代码块信息文本(value: string): string {
  return value.replace(/\s+/g, ' ').trim()
}
