import MarkdownIt from 'markdown-it'
import * as markdownItKatexModule from '@vscode/markdown-it-katex'
import { applyAuthorizedMarkdownImageRenderer } from './articleMedia'
import { 渲染Markdown代码高亮 } from './markdownHighlight'

type MarkdownItPlugin = (md: MarkdownIt, ...params: any[]) => void

const gridRenderer = new MarkdownIt({ html: true })
applyAuthorizedMarkdownImageRenderer(gridRenderer)

const articleRenderer = new MarkdownIt({
  html: true,
  linkify: true,
})
applyAuthorizedMarkdownImageRenderer(articleRenderer)
安全注册KaTeX插件(articleRenderer)

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
  if (信息.language.toLowerCase() === 'mermaid') {
    token.info = 信息.language
    return 默认代码块渲染(tokens, idx, options, env, self)
  }

  return 渲染增强代码块(token.content, 信息)
}

const ADMONITION_TYPES = [
  'note', 'tip', 'important', 'warning', 'caution',
  'abstract', 'summary', 'tldr', 'info', 'todo',
  'success', 'check', 'done', 'question', 'help', 'faq',
  'attention', 'failure', 'missing', 'fail', 'danger',
  'error', 'bug', 'example', 'quote', 'cite',
]

function 安全注册KaTeX插件(md: MarkdownIt) {
  const 插件 = 获取KaTeX插件()
  if (!插件) {
    console.warn('[Markdown] KaTeX 插件未能正确加载，已跳过公式渲染注册')
    return
  }

  try {
    md.use(插件)
  } catch (error) {
    console.error('[Markdown] KaTeX 插件注册失败，已跳过公式渲染注册', error)
  }
}

function 获取KaTeX插件(): MarkdownItPlugin | null {
  return 解析Markdown插件导出(markdownItKatexModule)
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
  <div id="${cardUuid}-description" class="gc-description">Waiting for api.github.com...</div>
  <div class="gc-infobar">
    <div id="${cardUuid}-stars" class="gc-stars">00K</div>
    <div id="${cardUuid}-forks" class="gc-forks">0K</div>
    <div id="${cardUuid}-license" class="gc-license">0K</div>
    <span id="${cardUuid}-language" class="gc-language">Waiting...</span>
  </div>
</a>
`.trim()
}

function preprocessGithubCards(raw: string): string {
  return raw.replace(/::github\{repo="([^"]+)"\}/g, (_match, repo) => {
    if (!repo.includes('/')) {
      return `<div class="hidden">Invalid repository. ("repo" must be in the format "owner/repo")</div>`
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
    if (line.includes('[grid]') && line.includes('[/grid]')) {
      const content = line.replace(/\[grid\]/, '').replace(/\[\/grid\]/, '')
      const html = gridRenderer.render(content)
      result.push(`<div class="image-grid">${html}</div>`)
      continue
    }

    if (/^\s*\[grid\]\s*$/.test(line)) {
      inGrid = true
      gridLines = []
      continue
    }

    if (/^\s*\[\/grid\]\s*$/.test(line)) {
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
    result.push('[grid]', ...gridLines)
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

    const match = trimmed.match(/^:::(\w+)(?:\[(.*?)\])?$/)
    if (match && !inAdmonition) {
      const type = match[1].toLowerCase()
      if (ADMONITION_TYPES.includes(type)) {
        inAdmonition = true
        admonitionType = type
        admonitionTitle = match[2] || ''
        admonitionLines = []
        continue
      }
    }

    if (trimmed === ':::' && inAdmonition) {
      inAdmonition = false
      const title = admonitionTitle || admonitionType.toUpperCase()
      result.push(`> [!${admonitionType.toUpperCase()}] ${title}`)
      for (const l of admonitionLines) {
        result.push(`> ${l}`)
      }
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
  return raw.replace(/:spoiler\[((?:[^\]\\]|\\.)*)\]/g, (_match, content) => {
    const html = gridRenderer.renderInline(content)
    return `<span class="spoiler" onclick="this.classList.toggle('revealed')">${html}</span>`
  })
}

export function preprocessMarkdown(raw: string): string {
  let processed = preprocessImageGrids(raw)
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
  language: string
  title: string
  highlightRanges: Array<[number, number]>
  showLineNumbers: boolean
}

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
      language: 'text',
      title: '',
      highlightRanges: [],
      showLineNumbers: false,
    }
  }

  const firstSpaceIndex = trimmed.search(/\s/)
  const language = firstSpaceIndex === -1 ? trimmed : trimmed.slice(0, firstSpaceIndex)
  const metadata = firstSpaceIndex === -1 ? '' : trimmed.slice(firstSpaceIndex).trim()
  const titleMatch = metadata.match(/\btitle=(?:"([^"]+)"|'([^']+)'|([^\s{}]+))/)
  const rangeMatch = metadata.match(/\{([^}]+)\}/)
  const showLineNumbers = /\b(showLineNumbers|lineNumbers|linenos|ln)\b/i.test(metadata)

  return {
    language: language || 'text',
    title: titleMatch?.[1] || titleMatch?.[2] || titleMatch?.[3] || '',
    highlightRanges: 解析代码高亮范围(rangeMatch?.[1] || ''),
    showLineNumbers,
  }
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
  const language = info.language || 'text'
  const 安全语言 = escapeHtml(language)
  const lines = code.replace(/\r\n/g, '\n').split('\n')
  if (lines.length > 1 && lines.at(-1) === '') {
    lines.pop()
  }

  const renderedLines = (lines.length > 0 ? lines : ['']).map((line, index) => {
    const lineNumber = index + 1
    const 高亮结果 = language ? 渲染Markdown代码高亮(line, language) : ''
    const lineHtml = 高亮结果 || (line.length > 0 ? escapeHtml(line) : '&nbsp;')
    const 高亮类名 = 命中代码高亮范围(lineNumber, info.highlightRanges) ? ' is-highlighted' : ''
    const 行号区块 = info.showLineNumbers
      ? `<span class="article-code-line-number" aria-hidden="true">${lineNumber}</span>`
      : ''

    return `<span class="article-code-line${高亮类名}">${行号区块}<span class="article-code-line-content">${lineHtml}</span></span>`
  }).join('\n')

  const 标题栏 = info.title
    ? `<div class="article-code-header"><span class="article-code-title">${escapeHtml(info.title)}</span><span class="article-code-language">${安全语言}</span></div>`
    : ''
  const 代码框类名 = info.title ? 'article-code-block article-code-block--with-header hljs' : 'article-code-block hljs'
  const 行号属性 = info.showLineNumbers ? ' data-line-numbers="true"' : ''

  return `<div class="article-code-frame">${标题栏}<pre class="${代码框类名}"><code class="hljs language-${安全语言}"${行号属性}>${renderedLines}</code></pre></div>`
}

function 命中代码高亮范围(lineNumber: number, ranges: Array<[number, number]>): boolean {
  return ranges.some(([start, end]) => lineNumber >= start && lineNumber <= end)
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}
