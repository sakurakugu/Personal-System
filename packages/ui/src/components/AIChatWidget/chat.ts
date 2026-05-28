import type { 聊天附件, 聊天消息 } from './types'

const 支持图片扩展名 = new Set([
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.gif',
  '.bmp',
  '.tiff',
  '.tif',
  '.heic',
  '.heif',
  '.svg',
])

export function 生成消息ID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function 获取文件扩展名(fileName: string): string {
  const extensionStart = fileName.lastIndexOf('.')
  if (extensionStart === -1) {
    return ''
  }
  return fileName.slice(extensionStart).toLowerCase()
}

export function 是否支持附件(file: File): boolean {
  const mimeType = file.type.toLowerCase()
  if (mimeType.startsWith('image/')) return true
  if (mimeType === 'application/pdf') return true
  const extension = 获取文件扩展名(file.name)
  return extension === '.pdf' || 支持图片扩展名.has(extension)
}

export function 格式化文件大小(sizeInBytes: number): string {
  if (sizeInBytes < 1024) return `${sizeInBytes} B`
  if (sizeInBytes < 1024 * 1024) return `${(sizeInBytes / 1024).toFixed(1)} KB`
  return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`
}

export function 生成附件(file: File): 聊天附件 {
  return {
    id: 生成消息ID(),
    file,
    filename: file.name,
    mediaType: file.type || 'application/octet-stream',
    size: file.size,
    url: URL.createObjectURL(file),
  }
}

export function 释放附件地址(attachments: readonly 聊天附件[]): void {
  for (const attachment of attachments) {
    if (attachment.url?.startsWith('blob:')) {
      URL.revokeObjectURL(attachment.url)
    }
  }
}

export function 转为接口消息(messages: 聊天消息[]) {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    parts: [
      ...(message.content ? [{ type: 'text', text: message.content }] : []),
      ...(message.attachments ?? []).map((attachment) => ({
        type: 'file',
        filename: attachment.filename,
        mediaType: attachment.mediaType,
        url: attachment.url,
      })),
    ],
  }))
}

export function 提取JSON文本(payload: unknown): string {
  if (typeof payload === 'string') return payload
  if (!payload || typeof payload !== 'object') return ''

  const record = payload as Record<string, unknown>
  if (typeof record.text === 'string') return record.text
  if (typeof record.content === 'string') return record.content
  if (typeof record.message === 'string') return record.message
  if (typeof record.delta === 'string') return record.delta
  if (typeof record.response === 'string') return record.response
  if (Array.isArray(record.parts)) return record.parts.map(提取JSON文本).join('')
  if (record.message && typeof record.message === 'object') return 提取JSON文本(record.message)
  if (Array.isArray(record.choices)) {
    return record.choices
      .map((choice) => {
        if (!choice || typeof choice !== 'object') return ''
        const item = choice as Record<string, unknown>
        return 提取JSON文本(item.delta) || 提取JSON文本(item.message)
      })
      .join('')
  }
  return ''
}

export function 解析数据流行(rawLine: string): string {
  const line = rawLine.trim()
  if (!line || line === 'data: [DONE]' || line === '[DONE]') return ''

  const payload = line.startsWith('data:') ? line.slice(5).trim() : line
  if (!payload || payload === '[DONE]') return ''

  try {
    return 提取JSON文本(JSON.parse(payload) as unknown)
  } catch {
    const sdkTextMatch = payload.match(/^\d+:(.*)$/)
    if (!sdkTextMatch) return payload
    try {
      return String(JSON.parse(sdkTextMatch[1] ?? '""'))
    } catch {
      return sdkTextMatch[1] ?? ''
    }
  }
}
