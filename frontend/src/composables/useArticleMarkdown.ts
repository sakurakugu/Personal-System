import { nextTick } from 'vue'

// ------------------------------------------------------------------
// Mermaid 增强（适配 Firefly 的客户端渲染脚本）
// ------------------------------------------------------------------

let mermaidInitialized = false
let currentMermaidTheme: string | null = null
let isRenderingMermaid = false
let mermaidRetryCount = 0
const MAX_RETRIES = 3
const RETRY_DELAY = 1000
const 已注册Mermaid容器 = new Set<HTMLElement>()

function hasThemeChanged() {
  const isDark = document.documentElement.classList.contains('dark')
  const newTheme = isDark ? 'dark' : 'default'
  if (currentMermaidTheme !== newTheme) {
    currentMermaidTheme = newTheme
    return true
  }
  return false
}

async function loadMermaid() {
  if (typeof window === 'undefined') return
  if ((window as any).mermaid) return
  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.12.0/mermaid.min.js'
    script.onload = () => resolve()
    script.onerror = () => {
      const fallback = document.createElement('script')
      fallback.src = 'https://unpkg.com/mermaid@11.12.0/dist/mermaid.min.js'
      fallback.onload = () => resolve()
      fallback.onerror = () => reject(new Error('Failed to load mermaid'))
      document.head.appendChild(fallback)
    }
    document.head.appendChild(script)
  })
}

async function loadSvgPanZoom() {
  if (typeof window === 'undefined') return
  if ((window as any).svgPanZoom) return
  return new Promise<void>((resolve) => {
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js'
    script.onload = () => resolve()
    script.onerror = () => {
      const fallback = document.createElement('script')
      fallback.src = 'https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js'
      fallback.onload = () => resolve()
      fallback.onerror = () => {
        console.warn('svg-pan-zoom load failed')
        resolve()
      }
      document.head.appendChild(fallback)
    }
    document.head.appendChild(script)
  })
}

function 获取有效Mermaid容器() {
  for (const container of 已注册Mermaid容器) {
    if (!container.isConnected) {
      已注册Mermaid容器.delete(container)
    }
  }

  return [...已注册Mermaid容器]
}

function destroyAllPanZoom(containers: Iterable<HTMLElement>) {
  for (const rootContainer of containers) {
    rootContainer.querySelectorAll('.mermaid-diagram-container[data-panzoom-init]').forEach((container) => {
      const c = container as any
      if (c._panZoomInstance) {
        try { c._panZoomInstance.destroy() } catch {}
        c._panZoomInstance = null
      }
      const controls = container.querySelector('.mermaid-controls')
      if (controls) controls.remove()
      container.removeAttribute('data-panzoom-init')
    })
  }
}

function openFullscreen(container: HTMLElement) {
  const svgElement = container.querySelector('.mermaid svg') as SVGElement | null
  if (!svgElement) return

  const overlay = document.createElement('div')
  overlay.className = 'mermaid-fullscreen-overlay'

  const content = document.createElement('div')
  content.className = 'mermaid-fs-content'

  const clonedSvg = svgElement.cloneNode(true) as SVGElement
  clonedSvg.style.filter = ''
  clonedSvg.setAttribute('width', '100%')
  clonedSvg.setAttribute('height', '100%')
  ;(clonedSvg.style as any).maxWidth = 'none'
  content.appendChild(clonedSvg)

  const fsControls = document.createElement('div')
  fsControls.className = 'mermaid-fs-controls'

  let fsInstance: any = null

  const closeOverlay = () => {
    if (fsInstance) {
      try { fsInstance.destroy() } catch {}
    }
    overlay.remove()
    document.removeEventListener('keydown', escHandler)
  }

  const escHandler = (e: KeyboardEvent) => {
    if (e.key === 'Escape') closeOverlay()
  }

  const fsButtons = [
    { label: '+', title: '放大', action: () => fsInstance?.zoomIn() },
    { label: '−', title: '缩小', action: () => fsInstance?.zoomOut() },
    { label: '↺', title: '重置', action: () => { fsInstance?.resetZoom(); fsInstance?.resetPan(); fsInstance?.center() } },
    { label: '✕', title: '关闭', action: closeOverlay },
  ]

  fsButtons.forEach((btn) => {
    const button = document.createElement('button')
    button.className = 'mermaid-ctrl-btn'
    button.textContent = btn.label
    button.title = btn.title
    button.addEventListener('click', (e) => {
      e.preventDefault()
      e.stopPropagation()
      btn.action()
    })
    fsControls.appendChild(button)
  })

  overlay.appendChild(content)
  overlay.appendChild(fsControls)
  document.body.appendChild(overlay)

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeOverlay()
  })
  document.addEventListener('keydown', escHandler)

  requestAnimationFrame(() => {
    try {
      fsInstance = (window as any).svgPanZoom(clonedSvg, {
        panEnabled: true,
        zoomEnabled: true,
        controlIconsEnabled: false,
        mouseWheelZoomEnabled: true,
        dblClickZoomEnabled: true,
        minZoom: 0.3,
        maxZoom: 10,
        fit: true,
        center: true,
        zoomScaleSensitivity: 0.3,
      })
    } catch (e) {
      console.warn('Fullscreen pan-zoom init failed', e)
    }
  })
}

function initPanZoom(containers: Iterable<HTMLElement>) {
  if (typeof document === 'undefined' || typeof (window as any).svgPanZoom !== 'function') return
  for (const rootContainer of containers) {
    rootContainer.querySelectorAll('.mermaid-diagram-container').forEach((container) => {
      if (container.hasAttribute('data-panzoom-init')) return
      const svgElement = container.querySelector('.mermaid svg') as SVGElement | null
      if (!svgElement || !svgElement.getAttribute('viewBox')) return

      const rect = svgElement.getBoundingClientRect()
      svgElement.setAttribute('width', `${rect.width}px`)
      svgElement.setAttribute('height', `${rect.height}px`)
      ;(svgElement.style as any).maxWidth = 'none'
      ;(svgElement.style as any).height = ''

      try {
        const panZoomInstance = (window as any).svgPanZoom(svgElement, {
          panEnabled: true,
          zoomEnabled: true,
          controlIconsEnabled: false,
          mouseWheelZoomEnabled: true,
          dblClickZoomEnabled: true,
          minZoom: 0.5,
          maxZoom: 5,
          fit: true,
          center: true,
          zoomScaleSensitivity: 0.3,
        })
        ;(container as any)._panZoomInstance = panZoomInstance
        container.setAttribute('data-panzoom-init', 'true')

        const controls = document.createElement('div')
        controls.className = 'mermaid-controls'
        const buttons = [
          { label: '+', title: '放大', action: () => panZoomInstance.zoomIn() },
          { label: '−', title: '缩小', action: () => panZoomInstance.zoomOut() },
          { label: '↺', title: '重置', action: () => { panZoomInstance.resetZoom(); panZoomInstance.resetPan(); panZoomInstance.center() } },
          { label: '⛶', title: '全屏', action: () => openFullscreen(container as HTMLElement) },
        ]
        buttons.forEach((btn) => {
          const b = document.createElement('button')
          b.className = 'mermaid-ctrl-btn'
          b.textContent = btn.label
          b.title = btn.title
          b.addEventListener('click', (e) => {
            e.preventDefault()
            e.stopPropagation()
            btn.action()
          })
          controls.appendChild(b)
        })
        container.appendChild(controls)
      } catch (e) {
        console.warn('Pan-zoom init failed', e)
      }
    })
  }
}

function 收集Mermaid元素(containers: Iterable<HTMLElement>) {
  const elements: HTMLElement[] = []
  for (const rootContainer of containers) {
    rootContainer.querySelectorAll('.mermaid[data-mermaid-code]').forEach((element) => {
      elements.push(element as HTMLElement)
    })
  }
  return elements
}

async function renderMermaidDiagrams(containers: Iterable<HTMLElement>) {
  if (isRenderingMermaid) return
  if (typeof document === 'undefined') return
  const mermaid = (window as any).mermaid
  if (!mermaid || typeof mermaid.render !== 'function') {
    console.warn('Mermaid not available')
    return
  }

  const elements = 收集Mermaid元素(containers)
  if (elements.length === 0) return

  isRenderingMermaid = true
  destroyAllPanZoom(containers)

  try {
    await new Promise((r) => setTimeout(r, 100))
    const isDark = document.documentElement.classList.contains('dark')
    const theme = isDark ? 'dark' : 'default'

    mermaid.initialize({
      startOnLoad: false,
      theme,
      themeVariables: {
        fontFamily: 'inherit',
        fontSize: '16px',
        primaryColor: isDark ? '#ffffff' : '#000000',
        primaryTextColor: isDark ? '#ffffff' : '#000000',
        primaryBorderColor: isDark ? '#ffffff' : '#000000',
        lineColor: isDark ? '#ffffff' : '#000000',
        secondaryColor: isDark ? '#333333' : '#f0f0f0',
        tertiaryColor: isDark ? '#555555' : '#e0e0e0',
      },
      securityLevel: 'loose',
      errorLevel: 'warn',
      logLevel: 'error',
    })

    const promises = elements.map(async (el, index) => {
      let attempts = 0
      const maxAttempts = 3
      while (attempts < maxAttempts) {
        try {
          const code = el.getAttribute('data-mermaid-code') || ''
          if (!code) break
          el.innerHTML = '<div class="mermaid-loading">Rendering diagram...</div>'
          const { svg } = await mermaid.render(`mermaid-${Date.now()}-${index}-${attempts}`, code)
          el.innerHTML = svg
          const svgElement = el.querySelector('svg')
          if (svgElement) {
            svgElement.setAttribute('width', '100%')
            svgElement.removeAttribute('height')
            ;(svgElement.style as any).maxWidth = '100%'
            ;(svgElement.style as any).height = 'auto'
            if (isDark) {
              svgElement.style.filter = 'brightness(0.9) contrast(1.1)'
            } else {
              svgElement.style.filter = 'none'
            }
          }
          break
        } catch (err) {
          attempts++
          console.warn(`Mermaid render attempt ${attempts} failed`, err)
          if (attempts >= maxAttempts) {
            el.innerHTML = `
              <div class="mermaid-error">
                <p>图表渲染失败</p>
                <button onclick="location.reload()" style="margin-top:8px;padding:4px 8px;background:var(--el-color-primary);color:#fff;border:none;border-radius:4px;cursor:pointer;">刷新重试</button>
              </div>
            `
          } else {
            await new Promise((r) => setTimeout(r, 500 * attempts))
          }
        }
      }
    })

    await Promise.all(promises)
    mermaidRetryCount = 0
    initPanZoom(containers)
  } catch (err) {
    console.error('Mermaid render error', err)
    if (mermaidRetryCount < MAX_RETRIES) {
      mermaidRetryCount++
      const activeContainers = 获取有效Mermaid容器()
      setTimeout(() => void renderMermaidDiagrams(activeContainers), RETRY_DELAY * mermaidRetryCount)
    }
  } finally {
    isRenderingMermaid = false
  }
}

async function initializeMermaid(container: HTMLElement) {
  try {
    await Promise.all([loadMermaid(), loadSvgPanZoom()])
    currentMermaidTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'default'
    await renderMermaidDiagrams([container])
  } catch (err) {
    console.error('Mermaid init failed', err)
    if (mermaidRetryCount < MAX_RETRIES) {
      mermaidRetryCount++
      setTimeout(() => void initializeMermaid(container), RETRY_DELAY * mermaidRetryCount)
    }
  }
}

function setupMermaidObserver() {
  if (typeof document === 'undefined' || mermaidInitialized) return
  mermaidInitialized = true

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const target = mutation.target as HTMLElement
        const wasDark = mutation.oldValue ? mutation.oldValue.includes('dark') : false
        const isDark = target.classList.contains('dark')
        if (wasDark !== isDark && hasThemeChanged()) {
          const activeContainers = 获取有效Mermaid容器()
          setTimeout(() => void renderMermaidDiagrams(activeContainers), 150)
        }
      }
    })
  })

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
    attributeOldValue: true,
  })

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      const activeContainers = 获取有效Mermaid容器()
      setTimeout(() => void renderMermaidDiagrams(activeContainers), 200)
    }
  })
}

function enhanceMermaid(container: HTMLElement) {
  const codeBlocks = container.querySelectorAll('pre code.language-mermaid')
  if (codeBlocks.length === 0) return

  codeBlocks.forEach((code) => {
    const pre = code.parentElement as HTMLPreElement
    const mermaidCode = code.textContent || ''
    const id = `mermaid-${Math.random().toString(36).slice(-6)}`

    const wrapper = document.createElement('div')
    wrapper.className = 'mermaid-diagram-container'
    wrapper.innerHTML = `
      <div class="mermaid-wrapper" id="${id}">
        <div class="mermaid" data-mermaid-code="${escapeHtml(mermaidCode)}"></div>
      </div>
    `
    pre.replaceWith(wrapper)
  })

  已注册Mermaid容器.add(container)
  setupMermaidObserver()
  void initializeMermaid(container)
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

// ------------------------------------------------------------------
// Admonition 增强（GitHub 风格 blockquote）
// ------------------------------------------------------------------

const ADMONITION_TYPES_SET = new Set([
  'NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION',
  'ABSTRACT', 'SUMMARY', 'TLDR', 'INFO', 'TODO',
  'SUCCESS', 'CHECK', 'DONE', 'QUESTION', 'HELP', 'FAQ',
  'ATTENTION', 'FAILURE', 'MISSING', 'FAIL', 'DANGER',
  'ERROR', 'BUG', 'EXAMPLE', 'QUOTE', 'CITE',
])

function enhanceAdmonitions(container: HTMLElement) {
  container.querySelectorAll('blockquote').forEach((bq) => {
    if (bq.classList.contains('admonition')) return
    const firstP = bq.querySelector('p')
    if (!firstP) return
    const text = firstP.textContent || ''
    const match = text.match(/^\[!(\w+)\]\s*(.*)$/)
    if (!match) return
    const type = match[1].toUpperCase()
    if (!ADMONITION_TYPES_SET.has(type)) return
    const title = match[2].trim() || type
    bq.classList.add('admonition', `bdm-${type.toLowerCase()}`)
    firstP.classList.add('bdm-title')
    firstP.textContent = title
  })
}

// ------------------------------------------------------------------
// GitHub Card 数据填充
// ------------------------------------------------------------------

function enhanceGithubCards(container: HTMLElement) {
  container.querySelectorAll('a.card-github.fetch-waiting').forEach((card) => {
    const el = card as HTMLElement
    const repo = el.getAttribute('data-github-repo')
    if (!repo || el.dataset.githubLoaded) return
    el.dataset.githubLoaded = 'true'

    const cardUuid = el.id
    fetch(`https://api.github.com/repos/${repo}`, { referrerPolicy: 'no-referrer' })
      .then((r) => r.json())
      .then((data) => {
        const desc = el.querySelector(`#${cardUuid}-description`)
        if (desc) desc.textContent = data.description?.replace(/:[a-zA-Z0-9_]+:/g, '') || '暂无描述'

        const lang = el.querySelector(`#${cardUuid}-language`)
        if (lang) lang.textContent = data.language || '-'

        const forks = el.querySelector(`#${cardUuid}-forks`)
        if (forks) forks.textContent = Intl.NumberFormat('en-us', { notation: 'compact', maximumFractionDigits: 1 }).format(data.forks).replaceAll('\u202f', '')

        const stars = el.querySelector(`#${cardUuid}-stars`)
        if (stars) stars.textContent = Intl.NumberFormat('en-us', { notation: 'compact', maximumFractionDigits: 1 }).format(data.stargazers_count).replaceAll('\u202f', '')

        const avatar = el.querySelector(`#${cardUuid}-avatar`) as HTMLElement | null
        if (avatar) {
          avatar.style.backgroundImage = `url(${data.owner.avatar_url}&s=32)`
          avatar.style.backgroundColor = 'transparent'
        }

        const license = el.querySelector(`#${cardUuid}-license`)
        if (license) license.textContent = data.license?.spdx_id || '无许可证'

        el.classList.remove('fetch-waiting')
      })
      .catch(() => {
        el.classList.add('fetch-error')
      })
  })
}

// ------------------------------------------------------------------
// Fancybox 绑定
// ------------------------------------------------------------------

async function bindFancybox(container: HTMLElement) {
  await import('@fancyapps/ui/dist/fancybox/fancybox.css')
  const { Fancybox } = await import('@fancyapps/ui')
  const options = {
    groupAll: true,
    Thumbs: { autoStart: true, showOnStart: 'yes' },
    Toolbar: {
      display: {
        left: ['infobar'],
        middle: ['zoomIn', 'zoomOut', 'toggle1to1', 'rotateCCW', 'rotateCW', 'flipX', 'flipY'],
        right: ['slideshow', 'thumbs', 'close'],
      },
    },
    animated: true,
    dragToClose: true,
    keyboard: {
      Escape: 'close',
      Delete: 'close',
      Backspace: 'close',
      PageUp: 'next',
      PageDown: 'prev',
      ArrowUp: 'next',
      ArrowDown: 'prev',
      ArrowRight: 'next',
      ArrowLeft: 'prev',
    },
    fitToView: true,
    preload: 3,
    infinite: true,
    Panzoom: { maxScale: 3, minScale: 1 },
    caption: false,
    Carousel: { transition: 'slide' },
  } as any

  Fancybox.close()
  Fancybox.unbind(container, '.article-markdown-preview img')
  Fancybox.bind(container, '.article-markdown-preview img', options)
  Fancybox.unbind('[data-fancybox="article-cover"]')
  Fancybox.bind('[data-fancybox="article-cover"]', options)
}

// ------------------------------------------------------------------
// Figure 包裹
// ------------------------------------------------------------------

function enhanceFigures(container: HTMLElement) {
  const images = container.querySelectorAll('img')
  images.forEach((img) => {
    if (img.closest('figure, .image-grid, .mermaid-diagram-container, a.card-github')) return
    const alt = img.getAttribute('alt')
    if (!alt || !alt.trim()) return

    const figure = document.createElement('figure')
    const newImg = img.cloneNode(true) as HTMLImageElement
    const figcaption = document.createElement('figcaption')
    figcaption.textContent = alt
    figure.appendChild(newImg)
    figure.appendChild(figcaption)

    const center = document.createElement('center')
    center.appendChild(figure)
    img.replaceWith(center)
  })
}

// ------------------------------------------------------------------
// 外部链接处理
// ------------------------------------------------------------------

function enhanceExternalLinks(container: HTMLElement) {
  const siteHost = typeof window !== 'undefined' ? window.location.host : ''
  container.querySelectorAll('a').forEach((a) => {
    const href = a.getAttribute('href')
    if (!href) return
    if (!href.startsWith('http://') && !href.startsWith('https://')) return
    try {
      if (siteHost && new URL(href).host === siteHost) return
    } catch {
      return
    }
    a.setAttribute('target', '_blank')
    a.setAttribute('rel', 'noopener noreferrer')
  })
}

// ------------------------------------------------------------------
// 邮件保护
// ------------------------------------------------------------------

function enhanceEmailProtection(container: HTMLElement) {
  container.querySelectorAll('a[href^="mailto:"]').forEach((a) => {
    const email = a.getAttribute('href')?.replace('mailto:', '') || ''
    if (!email) return
    const encoded = btoa(email)
    a.setAttribute('href', '#')
    a.setAttribute('data-encoded-email', encoded)
    a.addEventListener('click', function handler(e) {
      e.preventDefault()
      const encodedEmail = a.getAttribute('data-encoded-email')
      if (encodedEmail) {
        const decoded = atob(encodedEmail)
        a.setAttribute('href', `mailto:${decoded}`)
        a.removeEventListener('click', handler)
        ;(a as HTMLElement).click()
      }
    })
  })
}

// ------------------------------------------------------------------
// 统一入口
// ------------------------------------------------------------------

export function enhanceArticleMarkdown(container: HTMLElement) {
  nextTick(() => {
    enhanceMermaid(container)
    enhanceAdmonitions(container)
    enhanceGithubCards(container)
    enhanceFigures(container)
    enhanceExternalLinks(container)
    enhanceEmailProtection(container)
    void bindFancybox(container)
  })
}
