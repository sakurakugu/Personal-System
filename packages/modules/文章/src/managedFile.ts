import { 解析当前API基地址 } from '@personal-system/api'

const 站内文件路径前缀 = '/files/'

function isAbsoluteHttpUrl(value: string): boolean {
  return /^https?:\/\//i.test(value)
}

function buildManagedFileBaseUrl(): string {
  const apiBase = 解析当前API基地址()

  if (isAbsoluteHttpUrl(apiBase)) {
    return apiBase
  }

  if (typeof window !== 'undefined') {
    return window.location.origin
  }

  return apiBase
}

function parseManagedFileUrl(url: string): URL | null {
  const trimmedUrl = url.trim()
  if (!trimmedUrl) {
    return null
  }

  try {
    const parsed = isAbsoluteHttpUrl(trimmedUrl)
      ? new URL(trimmedUrl)
      : new URL(trimmedUrl, buildManagedFileBaseUrl())
    if (!parsed.pathname.startsWith(站内文件路径前缀)) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function resolveManagedFileUrl(url: string | null | undefined): string {
  if (!url) {
    return ''
  }

  const parsed = parseManagedFileUrl(url)
  if (parsed) {
    return parsed.toString()
  }
  return url
}

export function buildManagedFileThumbnailUrl(url: string | null | undefined, size: number = 144): string {
  if (!url) {
    return ''
  }

  const parsed = parseManagedFileUrl(url)
  if (!parsed) {
    return url
  }

  parsed.searchParams.set('thumbnail_width', String(size))
  parsed.searchParams.set('thumbnail_height', String(size))
  return parsed.toString()
}

export function extractManagedFilePath(url: string | null | undefined): string | null {
  if (!url) {
    return null
  }

  const parsed = parseManagedFileUrl(url)
  if (!parsed) {
    return null
  }

  return `${parsed.pathname}${parsed.hash}`
}
