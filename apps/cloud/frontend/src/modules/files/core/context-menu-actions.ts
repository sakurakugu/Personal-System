import {
  创建关闭右键菜单状态,
  创建文件夹右键菜单状态,
  创建空白右键菜单状态,
  创建资源右键菜单状态,
} from './context-menu'
import { 从目录树节点构建文件夹 } from './shared'
import type { 文件夹展示项, 右键菜单状态, 目录树节点, 资源展示项 } from './shared'

export function 处理资源行右键菜单触发(
  resource: 资源展示项,
  event: globalThis.MouseEvent,
  当前处于编辑态: boolean,
) {
  event.preventDefault()
  event.stopPropagation()
  if (当前处于编辑态) {
    return null
  }

  return 创建资源右键菜单状态(resource, event.clientX, event.clientY)
}

export function 处理文件夹右键菜单触发(
  folder: 文件夹展示项,
  event: globalThis.MouseEvent,
  source: 'tree' | 'list' = 'list',
) {
  event.preventDefault()
  event.stopPropagation()
  return 创建文件夹右键菜单状态(folder, event.clientX, event.clientY, source)
}

export function 处理目录树文件夹右键菜单触发(
  data: 目录树节点,
  event: globalThis.MouseEvent,
  重命名目录ID: string | null,
) {
  if (data.isRoot || data.isArticleImages || data.isDraft || 重命名目录ID === data.id) {
    return null
  }

  return 处理文件夹右键菜单触发(从目录树节点构建文件夹(data), event, 'tree')
}

export function 处理空白右键菜单触发(event: globalThis.MouseEvent) {
  if (event.defaultPrevented) {
    return null
  }

  event.preventDefault()
  return 创建空白右键菜单状态(event.clientX, event.clientY)
}

export function 获取关闭右键菜单后的状态(currentState: 右键菜单状态) {
  if (!currentState.visible) {
    return currentState
  }
  return 创建关闭右键菜单状态()
}
