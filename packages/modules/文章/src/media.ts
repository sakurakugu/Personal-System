import type MarkdownIt from 'markdown-it'
import { 构建管理文件缩略图URL, 解析管理文件URL地址 } from './managedFile'

export function 构建授权文件URL(url: string | null | undefined, accessToken?: string | null): string {
  void accessToken
  return 解析管理文件URL地址(url)
}

export function 构建文件缩略图URL(
  url: string | null | undefined,
  accessToken?: string | null,
  size: number = 144,
): string {
  void accessToken
  return 构建管理文件缩略图URL(url, size)
}

export function 构建授权文章资源URL(url: string | null | undefined, accessToken?: string | null): string {
  return 构建授权文件URL(url, accessToken)
}

export function 应用授权Markdown图片渲染器(md: MarkdownIt): void {
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
      imageToken.attrs[srcIndex][1] = 构建授权文件URL(imageToken.attrs[srcIndex][1])
    }
    imageToken.attrSet('loading', 'lazy')
    imageToken.attrSet('decoding', 'async')
    return fallbackRenderer(tokens, idx, options, env, self)
  }

  ;(wrappedRenderer as { __article_media_wrapped__?: boolean }).__article_media_wrapped__ = true
  rendererRules.image = wrappedRenderer
}
