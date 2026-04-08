import type MarkdownIt from 'markdown-it'

const 站内文件路径前缀 = '/files/'

function isAbsoluteUrl(url: string): boolean {
  return /^[a-z][a-z\d+\-.]*:\/\//i.test(url)
}

function isManagedFileUrl(target: URL): boolean {
  return target.origin === window.location.origin && target.pathname.startsWith(站内文件路径前缀)
}

function buildManagedFileUrl(
  url: string | null | undefined,
  queryParams?: Record<string, string>,
): string {
  if (!url || typeof window === 'undefined') {
    return url || ''
  }

  let target: URL
  try {
    target = new window.URL(url, window.location.origin)
  } catch {
    return url
  }

  if (!isManagedFileUrl(target)) {
    return url
  }

  Object.entries(queryParams ?? {}).forEach(([key, value]) => {
    target.searchParams.set(key, value)
  })

  if (!isAbsoluteUrl(url) && url.startsWith('/')) {
    return `${target.pathname}${target.search}${target.hash}`
  }

  return target.toString()
}

export function buildAuthorizedFileUrl(url: string | null | undefined, accessToken?: string | null): string {
  void accessToken
  return buildManagedFileUrl(url)
}

export function buildFileThumbnailUrl(
  url: string | null | undefined,
  accessToken?: string | null,
  size: number = 144,
): string {
  void accessToken
  return buildManagedFileUrl(url, {
    thumbnail_width: String(size),
    thumbnail_height: String(size),
  })
}

export function buildAuthorizedArticleAssetUrl(url: string | null | undefined, accessToken?: string | null): string {
  return buildAuthorizedFileUrl(url, accessToken)
}

export function applyAuthorizedMarkdownImageRenderer(md: MarkdownIt): void {
  const rendererRules = md.renderer.rules as Record<string, ((...args: any[]) => string) | undefined>
  const currentRenderer = rendererRules.image
  if ((currentRenderer as { __article_media_wrapped__?: boolean } | undefined)?.__article_media_wrapped__) {
    return
  }

  const fallbackRenderer = currentRenderer ?? ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))
  const wrappedRenderer = (tokens: any[], idx: number, options: any, env: any, self: any) => {
    const imageToken = tokens[idx]
    const srcIndex = imageToken.attrIndex('src')
    if (srcIndex >= 0 && imageToken.attrs?.[srcIndex]?.[1]) {
      imageToken.attrs[srcIndex][1] = buildAuthorizedFileUrl(imageToken.attrs[srcIndex][1])
    }
    return fallbackRenderer(tokens, idx, options, env, self)
  }

  ;(wrappedRenderer as { __article_media_wrapped__?: boolean }).__article_media_wrapped__ = true
  rendererRules.image = wrappedRenderer
}
