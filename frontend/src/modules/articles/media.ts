import type MarkdownIt from 'markdown-it'
import { buildManagedFileThumbnailUrl, resolveManagedFileUrl } from '../../utils/managedFile'

export function buildAuthorizedFileUrl(url: string | null | undefined, accessToken?: string | null): string {
  void accessToken
  return resolveManagedFileUrl(url)
}

export function buildFileThumbnailUrl(
  url: string | null | undefined,
  accessToken?: string | null,
  size: number = 144,
): string {
  void accessToken
  return buildManagedFileThumbnailUrl(url, size)
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
    imageToken.attrSet('loading', 'lazy')
    imageToken.attrSet('decoding', 'async')
    return fallbackRenderer(tokens, idx, options, env, self)
  }

  ;(wrappedRenderer as { __article_media_wrapped__?: boolean }).__article_media_wrapped__ = true
  rendererRules.image = wrappedRenderer
}
