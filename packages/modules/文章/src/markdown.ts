import MarkdownIt from 'markdown-it'
import markdownItAbbr from 'markdown-it-abbr'
import { 渲染Markdown代码高亮 } from './highlight'
import {
  MarkdownGithub卡片正则,
  Markdown仓库名称正则,
  Markdown剧透文本正则,
  Markdown容器提示块结束正则,
  Markdown容器提示块起始正则,
  Markdown折叠块匹配正则,
  Markdown提示块类型集合,
  Markdown提示块默认标题映射,
  Markdown标签页匹配正则,
  Markdown缩进提示块匹配正则,
  Markdown自定义语法Schema,
  获取Markdown代码块元数据Schema,
  type Markdown代码块框架,
} from './markdown-schema'
import { 应用授权Markdown图片渲染器 } from './media'

type MarkdownItPlugin = (md: MarkdownIt, ...params: any[]) => void

const gridRenderer = 创建Markdown渲染器()
const articleRenderer = 创建Markdown渲染器({ linkify: true, breaks: true })
const MarkdownMermaid语言 = 'mermaid'

const 默认表格打开渲染 =
  articleRenderer.renderer.rules.table_open
  ?? ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))
const 默认表格关闭渲染 =
  articleRenderer.renderer.rules.table_close
  ?? ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

articleRenderer.renderer.rules.table_open = (tokens, idx, options, env, self) => {
  return `<div class="horizontal-scroll-container">${默认表格打开渲染(tokens, idx, options, env, self)}`
}

articleRenderer.renderer.rules.table_close = (tokens, idx, options, env, self) => {
  return `${默认表格关闭渲染(tokens, idx, options, env, self)}</div>`
}

const 默认代码块渲染 =
  articleRenderer.renderer.rules.fence
  ?? ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

articleRenderer.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  const 信息 = 解析代码块信息(token.info)
  if (信息.language.toLowerCase() === MarkdownMermaid语言) {
    token.info = 信息.language
    return 默认代码块渲染(tokens, idx, options, env, self)
  }

  return 渲染增强代码块(token.content, 信息)
}

let MarkdownBlockSequence = 0
const 图片网格开始标记 = Markdown自定义语法Schema.imageGrid.openMarker
const 图片网格结束标记 = Markdown自定义语法Schema.imageGrid.closeMarker

function 创建Markdown渲染器(options: ConstructorParameters<typeof MarkdownIt>[0] = {}): MarkdownIt {
  const renderer = new MarkdownIt({
    html: true,
    ...options,
  })
  应用授权Markdown图片渲染器(renderer)
  安全注册Markdown插件(renderer, 获取缩写插件(), '缩写')
  return renderer
}

function 安全注册Markdown插件(
  md: MarkdownIt,
  插件: MarkdownItPlugin | null,
  插件名称: string,
  参数: unknown[] = [],
) {
  if (!插件) {
    console.warn(`[Markdown] ${插件名称} 插件未能正确加载，已跳过注册`)
    return
  }

  try {
    md.use(插件, ...参数)
  } catch (error) {
    console.error(`[Markdown] ${插件名称} 插件注册失败，已跳过注册`, error)
  }
}

function 获取缩写插件(): MarkdownItPlugin | null {
  return 解析Markdown插件导出(markdownItAbbr)
}

function 解析Markdown插件导出(候选值: unknown, 已访问 = new Set<unknown>()): MarkdownItPlugin | null {
  if (typeof 候选值 === 'function') {
    return 候选值 as MarkdownItPlugin
  }

  if (!候选值 || typeof 候选值 !== 'object' || 已访问.has(候选值)) {
    return null
  }

  已访问.add(候选值)

  const 默认导出 = (候选值 as { default?: unknown }).default
  return 解析Markdown插件导出(默认导出, 已访问)
}

function generateGithubCardHtml(repo: string): string {
  const cardUuid = `GC${Math.random().toString(36).slice(-6)}`
  const [owner, name] = repo.split('/')

  return `
<a id="${cardUuid}-card" class="card-github fetch-waiting no-styling" href="https://github.com/${repo}" target="_blank" data-github-repo="${repo}">
  <div class="gc-titlebar">
    <div class="gc-titlebar-left">
      <div class="gc-owner">
        <div id="${cardUuid}-avatar" class="gc-avatar"></div>
        <div class="gc-user">${owner}</div>
      </div>
      <div class="gc-divider">/</div>
      <div class="gc-repo">${name}</div>
    </div>
    <div class="github-logo"></div>
  </div>
  <div id="${cardUuid}-description" class="gc-description">正在请求 api.github.com...</div>
  <div class="gc-infobar">
    <div id="${cardUuid}-stars" class="gc-stars">00K</div>
    <div id="${cardUuid}-forks" class="gc-forks">0K</div>
    <div id="${cardUuid}-license" class="gc-license">0K</div>
    <span id="${cardUuid}-language" class="gc-language">等待中...</span>
  </div>
</a>
`.trim()
}

function preprocessGithubCards(raw: string): string {
  return raw.replace(MarkdownGithub卡片正则, (_match, repo) => {
    if (!Markdown仓库名称正则.test(repo)) {
      return `<div class="hidden">仓库格式错误（必须是 "owner/repo" 格式）</div>`
    }
    return generateGithubCardHtml(repo)
  })
}

function preprocessImageGrids(raw: string): string {
  const lines = raw.split('\n')
  const result: string[] = []
  let inGrid = false
  let gridLines: string[] = []
  let inCodeFence = false

  for (const line of lines) {
    const trimmed = line.trim()

    // 跟踪代码块，防止误判
    if (trimmed.startsWith('```')) {
      inCodeFence = !inCodeFence
      if (inGrid) {
        gridLines.push(line)
      } else {
        result.push(line)
      }
      continue
    }

    if (inCodeFence) {
      if (inGrid) {
        gridLines.push(line)
      } else {
        result.push(line)
      }
      continue
    }

    // 同一行包含 [grid] 和 [/grid]
    if (line.includes(图片网格开始标记) && line.includes(图片网格结束标记)) {
      const content = line.replace(图片网格开始标记, '').replace(图片网格结束标记, '')
      const html = gridRenderer.render(content)
      result.push(`<div class="image-grid">${html}</div>`)
      continue
    }

    if (trimmed === 图片网格开始标记) {
      inGrid = true
      gridLines = []
      continue
    }

    if (trimmed === 图片网格结束标记) {
      inGrid = false
      const html = gridRenderer.render(gridLines.join('\n'))
      result.push(`<div class="image-grid">${html}</div>`)
      continue
    }

    if (inGrid) {
      gridLines.push(line)
    } else {
      result.push(line)
    }
  }

  // 未闭合的 grid，原样放回
  if (inGrid) {
    result.push(图片网格开始标记, ...gridLines)
  }

  return result.join('\n')
}

function preprocessAdmonitions(raw: string): string {
  const lines = raw.split('\n')
  const result: string[] = []
  let inAdmonition = false
  let admonitionType = ''
  let admonitionTitle = ''
  let admonitionLines: string[] = []
  let inCodeFence = false

  for (const line of lines) {
    const trimmed = line.trim()

    if (trimmed.startsWith('```')) {
      inCodeFence = !inCodeFence
      if (inAdmonition) {
        admonitionLines.push(line)
      } else {
        result.push(line)
      }
      continue
    }

    if (inCodeFence) {
      if (inAdmonition) {
        admonitionLines.push(line)
      } else {
        result.push(line)
      }
      continue
    }

    const match = trimmed.match(Markdown容器提示块起始正则)
    if (match && !inAdmonition) {
      const type = match[1].toLowerCase()
      if (Markdown提示块类型集合.has(type)) {
        inAdmonition = true
        admonitionType = type
        admonitionTitle = match[2] || ''
        admonitionLines = []
        continue
      }
    }

    if (Markdown容器提示块结束正则.test(trimmed) && inAdmonition) {
      inAdmonition = false
      result.push(渲染Markdown提示块(admonitionType, admonitionTitle, admonitionLines.join('\n')))
      continue
    }

    if (inAdmonition) {
      admonitionLines.push(line)
    } else {
      result.push(line)
    }
  }

  if (inAdmonition) {
    result.push(`:::${admonitionType}${admonitionTitle ? `[${admonitionTitle}]` : ''}`, ...admonitionLines)
  }

  return result.join('\n')
}

function preprocessSpoilers(raw: string): string {
  return raw.replace(Markdown剧透文本正则, (_match, content) => {
    const html = gridRenderer.renderInline(content)
    return `<span class="spoiler" onclick="this.classList.toggle('revealed')">${html}</span>`
  })
}

function preprocessMarkdownBlocks(raw: string): string {
  const lines = raw.split('\n')
  const result: string[] = []
  let inCodeFence = false

  for (let index = 0; index < lines.length;) {
    const line = lines[index]
    const trimmed = line.trim()

    if (/^(```|~~~)/.test(trimmed)) {
      inCodeFence = !inCodeFence
      result.push(line)
      index += 1
      continue
    }

    if (inCodeFence) {
      result.push(line)
      index += 1
      continue
    }

    const indent = 计算行缩进宽度(line)
    const content = line.slice(获取首个非空白字符索引(line))
    const tabMatch = content.match(Markdown标签页匹配正则)
    if (tabMatch) {
      const 标签页组结果 = 解析Markdown标签页组(lines, index, indent)
      result.push(标签页组结果.html)
      index = 标签页组结果.nextIndex
      continue
    }

    const admonitionMatch = content.match(Markdown缩进提示块匹配正则)
    if (admonitionMatch) {
      const { content: body, nextIndex } = 提取缩进块(lines, index + 1, indent)
      result.push(渲染Markdown提示块(admonitionMatch[1], admonitionMatch[2] ?? '', body))
      index = nextIndex
      continue
    }

    const detailsMatch = content.match(Markdown折叠块匹配正则)
    if (detailsMatch) {
      const { content: body, nextIndex } = 提取缩进块(lines, index + 1, indent)
      result.push(渲染Markdown折叠块(detailsMatch[2], detailsMatch[3] ?? '', body, detailsMatch[1] === '???+'))
      index = nextIndex
      continue
    }

    result.push(line)
    index += 1
  }

  return result.join('\n')
}

function 解析Markdown标签页组(
  lines: string[],
  startIndex: number,
  parentIndent: number,
): { html: string; nextIndex: number } {
  const items: Array<{ title: string; content: string }> = []
  let index = startIndex

  while (index < lines.length) {
    const currentLine = lines[index]
    if (计算行缩进宽度(currentLine) !== parentIndent) {
      break
    }

    const currentContent = currentLine.slice(获取首个非空白字符索引(currentLine))
    const match = currentContent.match(Markdown标签页匹配正则)
    if (!match) {
      break
    }

    const { content, nextIndex } = 提取缩进块(lines, index + 1, parentIndent)
    items.push({
      title: 解析Markdown标题文本(match[1]),
      content,
    })
    index = nextIndex

    const tentativeIndex = 跳过空行(lines, index)
    if (tentativeIndex < lines.length) {
      const tentativeLine = lines[tentativeIndex]
      const tentativeContent = tentativeLine.slice(获取首个非空白字符索引(tentativeLine))
      if (
        计算行缩进宽度(tentativeLine) === parentIndent
        && Markdown标签页匹配正则.test(tentativeContent)
      ) {
        index = tentativeIndex
        continue
      }
    }

    break
  }

  return {
    html: 渲染Markdown标签页组(items),
    nextIndex: index,
  }
}

function 提取缩进块(
  lines: string[],
  startIndex: number,
  parentIndent: number,
): { content: string; nextIndex: number } {
  const collected: string[] = []
  let blockIndent: number | null = null
  let index = startIndex

  while (index < lines.length) {
    const line = lines[index]
    if (!line.trim()) {
      collected.push('')
      index += 1
      continue
    }

    const indent = 计算行缩进宽度(line)
    if (indent <= parentIndent) {
      break
    }

    if (blockIndent === null) {
      blockIndent = indent
    }

    if (indent < blockIndent) {
      break
    }

    collected.push(移除指定缩进(line, blockIndent))
    index += 1
  }

  return {
    content: collected.join('\n'),
    nextIndex: index,
  }
}

function 渲染Markdown提示块(type: string, rawTitle: string, body: string): string {
  const normalizedType = 规范化提示块类型(type)
  const title = rawTitle ? 解析Markdown标题文本(rawTitle) : 生成提示块默认标题(normalizedType)
  const contentHtml = 渲染Markdown片段(body)

  return `<div class="admonition bdm-${escapeHtml(normalizedType)}" data-admonition-type="${escapeHtml(normalizedType)}"><p class="bdm-title">${escapeHtml(title)}</p><div class="hello-algo-admonition__content">${contentHtml}</div></div>`
}

function 渲染Markdown折叠块(
  type: string,
  rawTitle: string,
  body: string,
  open: boolean,
): string {
  const normalizedType = 规范化提示块类型(type)
  const title = rawTitle ? 解析Markdown标题文本(rawTitle) : 生成提示块默认标题(normalizedType)
  const contentHtml = 渲染Markdown片段(body)
  const openAttr = open ? ' open' : ''

  return `<details class="admonition hello-algo-details bdm-${escapeHtml(normalizedType)}" data-admonition-type="${escapeHtml(normalizedType)}"${openAttr}><summary class="bdm-title">${escapeHtml(title)}</summary><div class="hello-algo-details__content">${contentHtml}</div></details>`
}

function 渲染Markdown标签页组(items: Array<{ title: string; content: string }>): string {
  if (items.length === 0) {
    return ''
  }

  const groupId = `hello-algo-tabs-${MarkdownBlockSequence += 1}`
  const html = items.map((item, index) => {
    const tabId = `${groupId}-tab-${index + 1}`
    const checkedAttr = index === 0 ? ' checked' : ''
    const contentHtml = 渲染Markdown片段(item.content)

    return `<input id="${tabId}" class="hello-algo-tabs__input" type="radio" name="${groupId}"${checkedAttr}><label class="hello-algo-tabs__label" for="${tabId}">${escapeHtml(item.title)}</label><div class="hello-algo-tabs__panel">${contentHtml}</div>`
  }).join('')

  return `<div class="hello-algo-tabs">${html}</div>`
}

function 渲染Markdown片段(raw: string): string {
  const processed = preprocessMarkdown(raw)
  return articleRenderer.render(processed)
}

function 规范化提示块类型(type: string): string {
  return type.trim().toLowerCase() || 'note'
}

function 生成提示块默认标题(type: string): string {
  return Markdown提示块默认标题映射[type] ?? 首字母大写(type)
}

function 解析Markdown标题文本(value: string): string {
  return value.replaceAll('\\"', '"').replaceAll('\\\\', '\\')
}

function 首字母大写(value: string): string {
  if (!value) {
    return ''
  }

  return value[0].toUpperCase() + value.slice(1)
}

function 计算行缩进宽度(line: string): number {
  let width = 0
  for (const char of line) {
    if (char === ' ') {
      width += 1
      continue
    }

    if (char === '\t') {
      width += 4
      continue
    }

    break
  }

  return width
}

function 获取首个非空白字符索引(line: string): number {
  const match = line.match(/[^\t ]/)
  return match?.index ?? line.length
}

function 移除指定缩进(line: string, indentWidth: number): string {
  let removed = 0
  let index = 0

  while (index < line.length && removed < indentWidth) {
    const char = line[index]
    if (char === ' ') {
      removed += 1
      index += 1
      continue
    }

    if (char === '\t') {
      removed += 4
      index += 1
      continue
    }

    break
  }

  return line.slice(index)
}

function 跳过空行(lines: string[], startIndex: number): number {
  let index = startIndex
  while (index < lines.length && !lines[index].trim()) {
    index += 1
  }
  return index
}

export function preprocessMarkdown(raw: string): string {
  let processed = raw
  processed = preprocessMarkdownBlocks(processed)
  processed = preprocessImageGrids(processed)
  processed = preprocessGithubCards(processed)
  processed = preprocessAdmonitions(processed)
  processed = preprocessSpoilers(processed)
  return processed
}

export interface RenderedMarkdownHeading {
  id: string
  text: string
  level: number
}

export interface RenderedArticleMarkdown {
  html: string
  headings: RenderedMarkdownHeading[]
}

interface CodeBlockInfo {
  hasFenceInfo: boolean
  language: string
  title: string
  highlightRanges: Array<[number, number]>
  insertedRanges: Array<[number, number]>
  deletedRanges: Array<[number, number]>
  showLineNumbers: boolean
  startLineNumber: number
  frame: Markdown代码块框架
  wrap: boolean
  preserveIndent: boolean
}

const 长代码自动折叠阈值 = Markdown自定义语法Schema.codeFence.autoCollapseLines
let 代码块折叠序号 = 0

interface InlineTextToken {
  content?: string
  children?: InlineTextToken[] | null
}

export function renderArticleMarkdown(
  raw: string,
  buildHeadingId: (index: number) => string = (index) => `heading-${index}`,
): RenderedArticleMarkdown {
  const processed = preprocessMarkdown(raw)
  const tokens = articleRenderer.parse(processed, {})
  const headings: RenderedMarkdownHeading[] = []
  let headingIndex = 0

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index]
    if (token.type !== 'heading_open') {
      continue
    }

    headingIndex += 1
    const level = Number.parseInt(token.tag.replace('h', ''), 10)
    const id = buildHeadingId(headingIndex)
    token.attrSet('id', id)
    headings.push({
      id,
      text: extractInlineText(tokens[index + 1] as InlineTextToken | undefined),
      level,
    })
  }

  return {
    html: articleRenderer.renderer.render(tokens, articleRenderer.options, {}),
    headings,
  }
}

function extractInlineText(token?: InlineTextToken): string {
  if (!token?.children?.length) {
    return ''
  }

  return token.children
    .map((child) => {
      if (child.content) {
        return child.content
      }

      if (child.children?.length) {
        return child.children.map((nested) => nested.content || '').join('')
      }

      return ''
    })
    .join('')
    .trim()
}

function 解析代码块信息(rawInfo: string): CodeBlockInfo {
  const trimmed = rawInfo.trim()
  if (!trimmed) {
    return {
      hasFenceInfo: false,
      language: Markdown自定义语法Schema.codeFence.defaultLanguage,
      title: '',
      highlightRanges: [],
      insertedRanges: [],
      deletedRanges: [],
      showLineNumbers: false,
      startLineNumber: 1,
      frame: Markdown自定义语法Schema.codeFence.defaultFrame,
      wrap: false,
      preserveIndent: false,
    }
  }

  const firstSpaceIndex = trimmed.search(/\s/)
  const language = firstSpaceIndex === -1 ? trimmed : trimmed.slice(0, firstSpaceIndex)
  const metadata = firstSpaceIndex === -1 ? '' : trimmed.slice(firstSpaceIndex).trim()
  const titleMatch = metadata.match(
    new RegExp(`\\b${获取代码块元数据别名('title')[0]}=(?:"([^"]+)"|'([^']+)'|([^\\s{}]+))`),
  )
  const highlightRanges = 解析范围元数据(metadata, 获取代码块元数据别名('highlight'))
    ?? 解析独立高亮范围(metadata)
  const showLineNumbers = 解析布尔元数据(metadata, 获取代码块元数据别名('lineNumbers'))
  const startLineNumber = 解析数字元数据(
    metadata,
    获取代码块元数据别名('startLineNumber'),
    1,
  )
  const frame = 解析代码块框架(metadata)
  const wrap = 解析布尔元数据(metadata, 获取代码块元数据别名('wrap'))
  const preserveIndent = 解析布尔元数据(metadata, 获取代码块元数据别名('preserveIndent'))
  const insertedRanges = 解析范围元数据(metadata, 获取代码块元数据别名('ins')) ?? []
  const deletedRanges = 解析范围元数据(metadata, 获取代码块元数据别名('del')) ?? []

  return {
    hasFenceInfo: true,
    language: language || Markdown自定义语法Schema.codeFence.defaultLanguage,
    title: titleMatch?.[1] || titleMatch?.[2] || titleMatch?.[3] || '',
    highlightRanges,
    insertedRanges,
    deletedRanges,
    showLineNumbers,
    startLineNumber,
    frame,
    wrap,
    preserveIndent,
  }
}

function 获取代码块元数据别名(name: string): readonly string[] {
  return 获取Markdown代码块元数据Schema(name)?.aliases ?? [name]
}

function 解析布尔元数据(rawMetadata: string, aliases: readonly string[]): boolean {
  for (const alias of aliases) {
    const explicitMatch = rawMetadata.match(new RegExp(`\\b${alias}=(true|false)\\b`, 'i'))
    if (explicitMatch) {
      return explicitMatch[1].toLowerCase() === 'true'
    }

    const standaloneMatch = rawMetadata.match(new RegExp(`\\b${alias}\\b`, 'i'))
    if (standaloneMatch) {
      return true
    }
  }

  return false
}

function 解析数字元数据(rawMetadata: string, aliases: readonly string[], fallback: number): number {
  for (const alias of aliases) {
    const match = rawMetadata.match(new RegExp(`\\b${alias}=(-?\\d+)\\b`, 'i'))
    if (!match) {
      continue
    }

    const parsed = Number.parseInt(match[1], 10)
    if (Number.isFinite(parsed)) {
      return Math.max(1, parsed)
    }
  }

  return fallback
}

function 解析代码块框架(rawMetadata: string): Markdown代码块框架 {
  const frameSchema = 获取Markdown代码块元数据Schema('frame')
  const frame = 解析枚举元数据(
    rawMetadata,
    frameSchema?.aliases ?? ['frame'],
    frameSchema?.allowedValues ?? Markdown自定义语法Schema.codeFence.frames,
  )
  if (frame === 'terminal' || frame === 'none') {
    return frame
  }

  return Markdown自定义语法Schema.codeFence.defaultFrame
}

function 解析枚举元数据(
  rawMetadata: string,
  aliases: readonly string[],
  allowedValues: readonly string[],
): string | null {
  for (const alias of aliases) {
    const match = rawMetadata.match(
      new RegExp(`\\b${alias}=(?:"([^"]+)"|'([^']+)'|([^\\s{}]+))`, 'i'),
    )
    const rawValue = match?.[1] || match?.[2] || match?.[3]
    if (!rawValue) {
      continue
    }

    const normalized = rawValue.toLowerCase()
    if (allowedValues.includes(normalized)) {
      return normalized
    }
  }

  return null
}

function 解析范围元数据(rawMetadata: string, aliases: readonly string[]): Array<[number, number]> | null {
  for (const alias of aliases) {
    const match = rawMetadata.match(new RegExp(`\\b${alias}=\\{([^}]+)\\}`, 'i'))
    if (!match) {
      continue
    }

    return 解析代码高亮范围(match[1])
  }

  return null
}

function 解析独立高亮范围(rawMetadata: string): Array<[number, number]> {
  const match = rawMetadata.match(/(?:^|\s)\{([^}]+)\}/)
  if (!match) {
    return []
  }

  return 解析代码高亮范围(match[1])
}

function 解析代码高亮范围(rawRanges: string): Array<[number, number]> {
  if (!rawRanges.trim()) {
    return []
  }

  return rawRanges
    .split(',')
    .map((segment) => segment.trim())
    .flatMap((segment) => {
      if (!segment) {
        return []
      }

      const [startText, endText] = segment.split('-').map((item) => item.trim())
      const start = Number.parseInt(startText, 10)
      const end = endText ? Number.parseInt(endText, 10) : start
      if (!Number.isFinite(start) || !Number.isFinite(end)) {
        return []
      }

      const normalizedStart = Math.max(1, Math.min(start, end))
      const normalizedEnd = Math.max(normalizedStart, Math.max(start, end))
      return [[normalizedStart, normalizedEnd] as [number, number]]
    })
}

function 渲染增强代码块(code: string, info: CodeBlockInfo): string {
  const language = info.language || Markdown自定义语法Schema.codeFence.defaultLanguage
  const 安全语言类名 = escapeHtml(language)
  const 语言展示文本 = escapeHtml(格式化代码语言标签(language))
  const 框架类型 = info.frame
  const 启用缩进保留 = info.wrap && info.preserveIndent
  const 显示行前导槽位 = info.showLineNumbers || info.insertedRanges.length > 0 || info.deletedRanges.length > 0
  const lines = code.replace(/\r\n/g, '\n').split('\n')
  if (lines.length > 1 && lines.at(-1) === '') {
    lines.pop()
  }
  const 需要自动折叠 = lines.length > 长代码自动折叠阈值

  const renderedLines = (lines.length > 0 ? lines : ['']).map((line, index) => {
    const lineNumber = index + 1
    const displayedLineNumber = info.startLineNumber + index
    const 高亮结果 = language ? 渲染Markdown代码高亮(line, language) : ''
    const lineHtml = 高亮结果 || (line.length > 0 ? escapeHtml(line) : '&nbsp;')
    const 是插入行 = 命中代码高亮范围(lineNumber, info.insertedRanges)
    const 是删除行 = 命中代码高亮范围(lineNumber, info.deletedRanges)
    const 行语义类名 = [
      命中代码高亮范围(lineNumber, info.highlightRanges) ? 'is-highlighted' : '',
      是插入行 ? 'is-inserted' : '',
      是删除行 ? 'is-deleted' : '',
    ].filter(Boolean).join(' ')
    const 行标记 = 是插入行 ? '+' : (是删除行 ? '-' : '')
    const 行号区块 = 显示行前导槽位
      ? `<span class="article-code-line-gutter" aria-hidden="true"><span class="article-code-line-marker">${行标记 || '&nbsp;'}</span>${info.showLineNumbers ? `<span class="article-code-line-number">${displayedLineNumber}</span>` : ''}</span>`
      : ''
    const 缩进宽度 = 启用缩进保留 ? 计算行首缩进宽度(line) : 0
    const 行内容类名 = [
      'article-code-line-content',
      启用缩进保留 && 缩进宽度 > 0 ? 'article-code-line-content--preserve-indent' : '',
    ].filter(Boolean).join(' ')
    const 行内容样式 = 启用缩进保留 && 缩进宽度 > 0
      ? ` style="--article-code-indent:${缩进宽度}"`
      : ''
    const 行类名 = ['article-code-line', 行语义类名].filter(Boolean).join(' ')

    return `<span class="${行类名}">${行号区块}<span class="${行内容类名}"${行内容样式}>${lineHtml}</span></span>`
  }).join('')

  const 显示标题栏 = 框架类型 !== 'none' && (info.hasFenceInfo || 框架类型 === 'terminal')
  const 标题栏标题 = info.title
    ? `<span class="article-code-title">${escapeHtml(info.title)}</span>`
    : ''
  const 标题栏控制区 = 框架类型 === 'terminal'
    ? '<span class="article-code-window-controls" aria-hidden="true"><span class="article-code-window-control"></span><span class="article-code-window-control"></span><span class="article-code-window-control"></span></span>'
    : ''
  const 标题栏 = 显示标题栏
    ? `<div class="article-code-header article-code-header--${框架类型}">${标题栏控制区}<span class="article-code-header-main">${标题栏标题}<span class="article-code-language">${语言展示文本}</span></span></div>`
    : ''
  const 代码框类名 = [
    'article-code-block',
    `article-code-block--${框架类型}`,
    显示标题栏 ? 'article-code-block--with-header' : '',
    info.wrap ? 'article-code-block--wrapped' : '',
    'hljs',
  ].filter(Boolean).join(' ')
  const 行号属性 = info.showLineNumbers ? ' data-line-numbers="true"' : ''
  const 前导槽位属性 = 显示行前导槽位 ? ' data-line-gutter="true"' : ''
  const 换行属性 = ` data-wrap="${info.wrap ? 'true' : 'false'}"`
  const 缩进属性 = ` data-preserve-indent="${启用缩进保留 ? 'true' : 'false'}"`
  const 代码块内容 = `<pre class="${代码框类名}" data-frame="${框架类型}"><code class="hljs language-${安全语言类名}"${行号属性}${前导槽位属性}${换行属性}${缩进属性}>${renderedLines}</code></pre>`
  const 可展示代码块内容 = 需要自动折叠
    ? 渲染可折叠代码块(代码块内容, lines.length, 框架类型)
    : 代码块内容

  if (框架类型 === 'none') {
    return 可展示代码块内容
  }

  return `<div class="article-code-frame article-code-frame--${框架类型}" data-frame="${框架类型}">${标题栏}${可展示代码块内容}</div>`
}

function 格式化代码语言标签(language: string): string {
  const normalized = language.trim().toLowerCase()
  const 语言标签映射: Record<string, string> = {
    c: 'C',
    h: 'C Header',
    cpp: 'C++',
    cc: 'C++',
    cxx: 'C++',
    hpp: 'C++ Header',
    hxx: 'C++ Header',
    cs: 'C#',
    csharp: 'C#',
    java: 'Java',
    kt: 'Kotlin',
    kotlin: 'Kotlin',
    swift: 'Swift',
    rs: 'Rust',
    rust: 'Rust',
    go: 'Go',
    golang: 'Go',
    php: 'PHP',
    rb: 'Ruby',
    ruby: 'Ruby',
    lua: 'Lua',
    perl: 'Perl',
    r: 'R',
    js: 'JavaScript',
    javascript: 'JavaScript',
    jsx: 'JSX',
    ts: 'TypeScript',
    tsx: 'TSX',
    mts: 'TypeScript',
    cts: 'TypeScript',
    py: 'Python',
    python: 'Python',
    toml: 'TOML',
    ini: 'INI',
    conf: 'Config',
    env: 'Environment',
    sh: 'Shell',
    shell: 'Shell',
    bash: 'Bash',
    zsh: 'Zsh',
    fish: 'Fish',
    console: 'Console',
    terminal: 'Terminal',
    powershell: 'PowerShell',
    ps1: 'PowerShell',
    bat: 'Batch',
    cmd: 'Batch',
    yml: 'YAML',
    yaml: 'YAML',
    md: 'Markdown',
    markdown: 'Markdown',
    html: 'HTML',
    htm: 'HTML',
    css: 'CSS',
    scss: 'SCSS',
    sass: 'Sass',
    less: 'Less',
    stylus: 'Stylus',
    vue: 'Vue',
    json: 'JSON',
    jsonc: 'JSONC',
    xml: 'XML',
    sql: 'SQL',
    graphql: 'GraphQL',
    gql: 'GraphQL',
    dockerfile: 'Dockerfile',
    makefile: 'Makefile',
    gitignore: '.gitignore',
    nginx: 'Nginx',
    apache: 'Apache',
    diff: 'Diff',
    patch: 'Patch',
    plaintext: 'Text',
    text: 'Text',
    txt: 'Text',
  }

  return 语言标签映射[normalized] || language
}

function 渲染可折叠代码块(
  codeBlockHtml: string,
  lineCount: number,
  frame: Markdown代码块框架,
): string {
  const 折叠控件ID = `article-code-collapse-${代码块折叠序号 += 1}`
  const 剩余行数 = Math.max(0, lineCount - 长代码自动折叠阈值)
  const 展开文案 = 剩余行数 > 0
    ? `展开剩余 ${剩余行数} 行`
    : `展开代码（共 ${lineCount} 行）`

  return `<div class="article-code-collapse article-code-collapse--${frame}" style="--article-code-collapse-preview-lines:${长代码自动折叠阈值}"><input id="${折叠控件ID}" class="article-code-collapse-input" type="checkbox"><div class="article-code-collapse-content">${codeBlockHtml}</div><label class="article-code-collapse-toggle" for="${折叠控件ID}"><span class="article-code-collapse-toggle-collapsed">${展开文案}</span><span class="article-code-collapse-toggle-expanded">收起代码</span></label></div>`
}

function 命中代码高亮范围(lineNumber: number, ranges: Array<[number, number]>): boolean {
  return ranges.some(([start, end]) => lineNumber >= start && lineNumber <= end)
}

function 计算行首缩进宽度(line: string): number {
  let width = 0
  for (const char of line) {
    if (char === ' ') {
      width += 1
      continue
    }

    if (char === '\t') {
      width += 2
      continue
    }

    break
  }

  return width
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}
