import type { 文件夹展示项, 文件展示项, 右键菜单状态, 资源展示项 } from './shared'

export function 创建关闭右键菜单状态(): 右键菜单状态 {
  return {
    visible: false,
    x: 0,
    y: 0,
    scope: 'blank',
    source: 'blank',
    resource: null,
  }
}

export function 创建文件右键菜单状态(file: 文件展示项, x: number, y: number): 右键菜单状态 {
  return {
    visible: true,
    x,
    y,
    scope: 'file',
    source: 'list',
    resource: { type: 'file', id: file.id },
  }
}

export function 创建文件夹右键菜单状态(
  folder: 文件夹展示项,
  x: number,
  y: number,
  source: 'tree' | 'list' = 'list',
): 右键菜单状态 {
  return {
    visible: true,
    x,
    y,
    scope: 'folder',
    source,
    resource: { type: 'folder', id: folder.id },
  }
}

export function 创建空白右键菜单状态(x: number, y: number): 右键菜单状态 {
  return {
    visible: true,
    x,
    y,
    scope: 'blank',
    source: 'blank',
    resource: null,
  }
}

export function 创建资源右键菜单状态(resource: 资源展示项, x: number, y: number): 右键菜单状态 {
  if (resource.type === 'folder') {
    return 创建文件夹右键菜单状态(resource.item, x, y)
  }
  if (resource.type === 'trash') {
    return 创建关闭右键菜单状态()
  }
  return 创建文件右键菜单状态(resource.item, x, y)
}
