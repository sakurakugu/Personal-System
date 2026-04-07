import type MarkdownIt from 'markdown-it'

const 文件访问令牌参数名 = 'access_token'
const 站内文件路径前缀 = '/files/'

function isAbsoluteUrl(url: string): boolean {
  return /^[a-z][a-z\d+\-.]*:\/\//i.test(url)
}

function isManagedFileUrl(target: URL): boolean {
  return target.origin === window.location.origin && target.pathname.startsWith(站内文件路径前缀)
}

export function getStoredAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return window.localStorage.getItem('access_token')
}

export function buildAuthorizedArticleAssetUrl(url: string | null | undefined, accessToken?: string | null): string {
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

  if (accessToken) {
    target.searchParams.set(文件访问令牌参数名, accessToken)
  } else {
    target.searchParams.delete(文件访问令牌参数名)
  }

  if (!isAbsoluteUrl(url) && url.startsWith('/')) {
    return `${target.pathname}${target.search}${target.hash}`
  }

  return target.toString()
}

export function applyAuthorizedMarkdownImageRenderer(
  md: MarkdownIt,
  getAccessToken: () => string | null | undefined,
): void {
  const rendererRules = md.renderer.rules as Record<string, ((...args: any[]) => string) | undefined>
  const currentRenderer = rendererRules.image
  if ((currentRenderer as { __article_media_wrapped__?: boolean } | undefined)?.__article_media_wrapped__) {
    return
  }

  const fallbackRenderer = currentRenderer ?? ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))
  const wrappedRenderer = (tokens: any[], idx: number, options: any, env: any, self: any) => {
    const token = getAccessToken()
    const imageToken = tokens[idx]
    const srcIndex = imageToken.attrIndex('src')
    if (srcIndex >= 0 && imageToken.attrs?.[srcIndex]?.[1]) {
      imageToken.attrs[srcIndex][1] = buildAuthorizedArticleAssetUrl(imageToken.attrs[srcIndex][1], token)
    }
    return fallbackRenderer(tokens, idx, options, env, self)
  }

  ;(wrappedRenderer as { __article_media_wrapped__?: boolean }).__article_media_wrapped__ = true
  rendererRules.image = wrappedRenderer
}
