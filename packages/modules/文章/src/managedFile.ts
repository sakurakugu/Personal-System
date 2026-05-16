import { 解析当前API基地址 } from '@personal-system/api'

const 站内文件路径前缀 = '/files/'

function 是否是绝对HTTP地址(value: string): boolean {
  return /^https?:\/\//i.test(value)
}

function 构建管理文件基础URL(): string {
  const apiBase = 解析当前API基地址()

  if (是否是绝对HTTP地址(apiBase)) {
    return apiBase
  }

  if (typeof window !== 'undefined') {
    return window.location.origin
  }

  return apiBase
}

function 解析管理文件URL(url: string): URL | null {
  const trimmedUrl = url.trim()
  if (!trimmedUrl) {
    return null
  }

  try {
    const parsed = 是否是绝对HTTP地址(trimmedUrl)
      ? new URL(trimmedUrl)
      : new URL(trimmedUrl, 构建管理文件基础URL())
    if (!parsed.pathname.startsWith(站内文件路径前缀)) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function 解析管理文件URL地址(url: string | null | undefined): string {
  if (!url) {
    return ''
  }

  const parsed = 解析管理文件URL(url)
  if (parsed) {
    return parsed.toString()
  }
  return url
}

export function 构建管理文件缩略图URL(url: string | null | undefined, size: number = 144): string {
  if (!url) {
    return ''
  }

  const parsed = 解析管理文件URL(url)
  if (!parsed) {
    return url
  }

  parsed.searchParams.set('thumbnail_width', String(size))
  parsed.searchParams.set('thumbnail_height', String(size))
  return parsed.toString()
}

export function 提取管理文件路径(url: string | null | undefined): string | null {
  if (!url) {
    return null
  }

  const parsed = 解析管理文件URL(url)
  if (!parsed) {
    return null
  }

  return `${parsed.pathname}${parsed.hash}`
}
