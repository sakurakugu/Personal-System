import MarkdownIt from 'markdown-it'
import { applyAuthorizedMarkdownImageRenderer } from './articleMedia'

const gridRenderer = new MarkdownIt({ html: true })
applyAuthorizedMarkdownImageRenderer(gridRenderer)

const ADMONITION_TYPES = [
  'note', 'tip', 'important', 'warning', 'caution',
  'abstract', 'summary', 'tldr', 'info', 'todo',
  'success', 'check', 'done', 'question', 'help', 'faq',
  'attention', 'failure', 'missing', 'fail', 'danger',
  'error', 'bug', 'example', 'quote', 'cite',
]

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
