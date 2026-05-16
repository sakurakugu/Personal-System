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
