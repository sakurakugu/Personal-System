import { Document, Picture } from '@element-plus/icons-vue'
import { extractManagedFilePath, resolveManagedFileUrl } from '../managed-file'
import { 文章图片标签, 动态图片标签 } from './shared'
import type { 文件展示项, 资源展示项 } from './shared'

export function 解析链接(url: string) {
  return resolveManagedFileUrl(url)
}

export function 获取可预览文件链接(url: string) {
  return resolveManagedFileUrl(url)
}

export function 获取图片缩略图链接(file: 文件展示项) {
  return resolveManagedFileUrl(file.thumbnail_url || file.url)
}

export function 获取原始文件路径(url: string) {
  return extractManagedFilePath(url) || url
}

export function 格式化大小(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export function 格式化时间(value: string) {
  return new Date(value).toLocaleString()
}

export function 提取扩展名(filename: string) {
  return filename.split('.').pop()?.trim().toLowerCase() || ''
}

export function 是否文章图片(file: 文件展示项) {
  return file.purpose === 'article_image'
}

export function 是否动态图片(file: 文件展示项) {
  return file.purpose === 'moment_image'
}

export function 是否内容图片(file: 文件展示项) {
  return 是否文章图片(file) || 是否动态图片(file)
}

export function 是否普通文件(file: 文件展示项) {
  return file.purpose === 'file'
}

export function 是否可移动文件(file: 文件展示项) {
  return 是否普通文件(file)
}

export function 是否图片(file: 文件展示项) {
  return file.mime_type.startsWith('image/')
}

export function 是否视频(file: 文件展示项) {
  return file.mime_type.startsWith('video/')
}

export function 是否可预览媒体(file: 文件展示项) {
  return 是否图片(file) || 是否视频(file)
}

export function 获取文件用途标签(file: 文件展示项) {
  if (是否文章图片(file)) {
    return 文章图片标签
  }
  if (是否动态图片(file)) {
    return 动态图片标签
  }
  return ''
}

export function 获取文件附加说明(file: 文件展示项) {
  if (是否文章图片(file) && file.article_title) {
    return `所属文章：${file.article_title}`
  }
  if (是否动态图片(file) && file.moment_title) {
    return `所属动态：${file.moment_title}`
  }
  return ''
}

export function 获取文件标签(file: 文件展示项) {
  const extension = 提取扩展名(file.original_name)
  if (extension) {
    return extension.toUpperCase()
  }
  if (file.mime_type.startsWith('image/')) {
    return 'IMG'
  }
  return 'FILE'
}

export function 获取文件图标(file: 文件展示项) {
  return 是否图片(file) ? Picture : Document
}

export function 是否文件夹资源(resource: 资源展示项): resource is Extract<资源展示项, { type: 'folder' }> {
  return resource.type === 'folder'
}

export function 是否文件资源(resource: 资源展示项): resource is Extract<资源展示项, { type: 'file' }> {
  return resource.type === 'file'
}

export function 获取资源附加说明(resource: 资源展示项) {
  if (resource.type === 'folder') {
    return ''
  }
  return 获取文件附加说明(resource.item)
}

export function 获取资源路径(resource: 资源展示项, 是否全局搜索模式: boolean) {
  if (!是否全局搜索模式) {
    return ''
  }
  return 'path' in resource.item ? resource.item.path : ''
}

export function 获取资源主标签(resource: 资源展示项) {
  if (resource.type === 'folder') {
    return '文件夹'
  }
  return 获取文件标签(resource.item)
}

export function 获取资源用途标签(resource: 资源展示项) {
  if (resource.type === 'folder') {
    return ''
  }
  return 获取文件用途标签(resource.item)
}

export function 是否可拖拽资源(resource: 资源展示项, 是否全局搜索模式: boolean) {
  if (是否全局搜索模式) {
    return false
  }
  if (resource.type === 'folder') {
    return true
  }
  return 是否可移动文件(resource.item)
}
