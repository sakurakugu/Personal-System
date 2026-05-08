import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '@personal-system/api'
import {
  downloadArchive as requestDownloadArchive,
  downloadFile as requestDownloadFile,
} from '../api'
import { resolveManagedFileUrl } from '../managed-file'
import { 提取资源ID列表 } from './operations'
import type {
  文件夹展示项,
  文件展示项,
  资源标识,
} from './shared'

interface 下载资源参数 {
  资源列表: 资源标识[]
  当前目录名称: string
  是否全局搜索模式: boolean
  查找文件夹展示项: (id: string) => 文件夹展示项 | null
  查找文件展示项: (id: string) => 文件展示项 | null
}

export interface 媒体预览状态 {
  当前预览媒体ID: string
  媒体预览对话框可见: boolean
}

type 图片预览项 = {
  src: string
  thumbSrc: string
  type: 'image'
  caption: string
}

type 图片预览实例 = {
  close: () => void
  show: (items: 图片预览项[], options?: Record<string, unknown>) => void
}

const 图片预览选项 = {
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
} as const

let Fancybox实例: 图片预览实例 | null = null

function 去掉末尾压缩包扩展名(name: string) {
  return name.replace(/\.zip$/i, '')
}

function 去掉最后一个扩展名(name: string) {
  const lastDotIndex = name.lastIndexOf('.')
  if (lastDotIndex <= 0) {
    return name
  }
  return name.slice(0, lastDotIndex)
}

export function 构建压缩包名称({
  资源列表,
  当前目录名称,
  是否全局搜索模式,
  查找文件夹展示项,
  查找文件展示项,
}: 下载资源参数) {
  if (资源列表.length === 1) {
    const resource = 资源列表[0]
    if (resource.type === 'folder') {
      const folder = 查找文件夹展示项(resource.id)
      return 去掉末尾压缩包扩展名(folder?.name?.trim() || '资源打包')
    }

    const file = 查找文件展示项(resource.id)
    return 去掉末尾压缩包扩展名(去掉最后一个扩展名(file?.original_name?.trim() || '资源打包'))
  }

  if (是否全局搜索模式) {
    return `搜索结果-${资源列表.length}项`
  }

  return 去掉末尾压缩包扩展名(当前目录名称 || '资源打包')
}

function 触发浏览器下载(blob: globalThis.Blob, fileName: string) {
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = fileName
  document.body.append(link)
  link.click()
  link.remove()
  window.setTimeout(() => {
    window.URL.revokeObjectURL(downloadUrl)
  }, 0)
}

export function 获取单文件下载项(
  资源列表: 资源标识[],
  查找文件展示项: (id: string) => 文件展示项 | null,
) {
  if (资源列表.length !== 1 || 资源列表[0]?.type !== 'file') {
    return null
  }

  return 查找文件展示项(资源列表[0].id)
}

async function 获取图片预览实例() {
  if (Fancybox实例) {
    return Fancybox实例
  }

  const [{ Fancybox }] = await Promise.all([
    import('@fancyapps/ui'),
    import('@fancyapps/ui/dist/fancybox/fancybox.css'),
  ])

  Fancybox实例 = Fancybox as unknown as 图片预览实例
  return Fancybox实例
}

async function 直接下载文件(file: 文件展示项) {
  try {
    const blob = await requestDownloadFile(file.url)
    触发浏览器下载(blob, file.original_name)
    ElMessage.success('文件已开始下载')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '文件下载失败'))
  }
}

export async function 执行资源下载(params: 下载资源参数) {
  const 单文件下载项 = 获取单文件下载项(params.资源列表, params.查找文件展示项)
  if (单文件下载项) {
    await 直接下载文件(单文件下载项)
    return
  }

  const { 文件ID列表, 文件夹ID列表 } = 提取资源ID列表(params.资源列表)
  const archiveName = 构建压缩包名称(params)

  try {
    const blob = await requestDownloadArchive(文件夹ID列表, 文件ID列表, archiveName)
    触发浏览器下载(blob, `${archiveName}.zip`)
    ElMessage.success('压缩包已开始下载')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '打包下载失败'))
  }
}

export function 创建媒体预览状态(file: 文件展示项): 媒体预览状态 {
  return {
    当前预览媒体ID: file.id,
    媒体预览对话框可见: true,
  }
}

export async function 打开图片预览(file: 文件展示项, 图片列表: 文件展示项[]) {
  const startIndex = 图片列表.findIndex((item) => item.id === file.id)
  if (startIndex < 0) {
    return
  }

  const Fancybox = await 获取图片预览实例()
  const items: 图片预览项[] = 图片列表.map((item) => ({
    src: resolveManagedFileUrl(item.url),
    thumbSrc: resolveManagedFileUrl(item.thumbnail_url || item.url),
    type: 'image',
    caption: item.original_name,
  }))

  Fancybox.show(items, {
    ...图片预览选项,
    startIndex,
  })
}

export function 关闭图片预览() {
  Fancybox实例?.close()
}

export function 计算切换后的预览媒体ID(
  当前预览媒体索引: number,
  step: number,
  可预览媒体文件列表: 文件展示项[],
) {
  if (当前预览媒体索引 < 0) {
    return null
  }

  const nextIndex = 当前预览媒体索引 + step
  if (nextIndex < 0 || nextIndex >= 可预览媒体文件列表.length) {
    return null
  }

  return 可预览媒体文件列表[nextIndex]?.id ?? null
}

