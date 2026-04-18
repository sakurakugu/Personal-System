import type {
  FileFolderItem,
  FileItem,
  FileSearchFileItem,
  FileSearchFolderItem,
  FileTreeNode,
} from '../types'

export type 资源类型 = 'folder' | 'file'
export type 右键菜单范围 = 'blank' | 'folder' | 'file'
export type 排序方式 = 'name-asc' | 'name-desc' | 'time-desc' | 'time-asc' | 'size-desc' | 'size-asc'
export type 搜索范围 = 'current' | 'global'
export type 文件夹展示项 = FileFolderItem | FileSearchFolderItem
export type 文件展示项 = FileItem | FileSearchFileItem
export type 资源展示项 =
  | { type: 'folder'; id: string; item: 文件夹展示项 }
  | { type: 'file'; id: string; item: 文件展示项 }
export type 带目录路径文件 = globalThis.File & {
  webkitRelativePath?: string
}

export interface 资源标识 {
  type: 资源类型
  id: string
}

export interface 目录树节点 extends FileTreeNode {
  isRoot?: boolean
  isArticleImages?: boolean
  isDraft?: boolean
}

export interface 右键菜单状态 {
  visible: boolean
  x: number
  y: number
  scope: 右键菜单范围
  source: 'blank' | 'tree' | 'list'
  resource: 资源标识 | null
}

export interface 新建目录草稿 {
  id: string
  parentId: string | null
  name: string
}

export interface 右侧新建文件夹草稿 {
  id: string
  parentId: string | null
  name: string
}

export interface 重命名目录草稿 {
  id: string
  name: string
  originalName: string
}

export interface 列表重命名草稿 {
  type: 资源类型
  id: string
  name: string
  originalName: string
}

export interface 拉取资源选项 {
  静默?: boolean
}

export const 根目录节点键 = '__root__'
export const 文章图片节点键 = '__article_images__'
export const 拖拽数据类型 = 'application/x-web-system-resource'
export const 根目录名称 = '全部文件'
export const 最小目录树宽度 = 220
export const 最大目录树宽度 = 520
export const 最小主区域宽度 = 420
export const 分隔线宽度 = 20
export const 文章图片标签 = '文章图片'
export const 桌面端初始渲染资源数量 = 80
export const 桌面端增量渲染资源数量 = 60
export const 移动端初始渲染资源数量 = 32
export const 移动端增量渲染资源数量 = 24
export const 新建目录临时节点键 = '__creating_folder__'
export const 右侧新建文件夹临时资源键 = '__creating_folder_in_list__'
export const 排序选项 = [
  { label: '名称 A-Z', value: 'name-asc' },
  { label: '名称 Z-A', value: 'name-desc' },
  { label: '时间 新到旧', value: 'time-desc' },
  { label: '时间 旧到新', value: 'time-asc' },
  { label: '大小 大到小', value: 'size-desc' },
  { label: '大小 小到大', value: 'size-asc' },
] as const
export const 搜索范围选项 = [
  { label: '当前目录', value: 'current' },
  { label: '跨目录', value: 'global' },
] as const

export function 是否匹配搜索关键词(name: string, keyword: string) {
  const normalizedKeyword = keyword.trim().toLowerCase()
  if (!normalizedKeyword) {
    return true
  }
  return name.toLowerCase().includes(normalizedKeyword)
}

export function 比较文本(a: string, b: string) {
  return a.localeCompare(b, 'zh-CN', { numeric: true, sensitivity: 'base' })
}

export function 比较时间(a: string, b: string) {
  return new Date(a).getTime() - new Date(b).getTime()
}

export function 排序文件夹列表(source: FileFolderItem[], 当前排序: 排序方式) {
  const sorted = [...source]
  sorted.sort((left, right) => {
    switch (当前排序) {
      case 'name-desc':
        return 比较文本(right.name, left.name)
      case 'time-desc':
        return 比较时间(right.updated_at, left.updated_at)
      case 'time-asc':
        return 比较时间(left.updated_at, right.updated_at)
      default:
        return 比较文本(left.name, right.name)
    }
  })
  return sorted
}

export function 排序文件列表(source: FileItem[], 当前排序: 排序方式) {
  const sorted = [...source]
  sorted.sort((left, right) => {
    switch (当前排序) {
      case 'name-desc':
        return 比较文本(right.original_name, left.original_name)
      case 'time-desc':
        return 比较时间(right.created_at, left.created_at)
      case 'time-asc':
        return 比较时间(left.created_at, right.created_at)
      case 'size-desc':
        return right.size - left.size
      case 'size-asc':
        return left.size - right.size
      default:
        return 比较文本(left.original_name, right.original_name)
    }
  })
  return sorted
}

function 比较资源类型(left: 资源展示项, right: 资源展示项) {
  if (left.type === right.type) {
    return 0
  }
  return left.type === 'folder' ? -1 : 1
}

function 获取资源名称(resource: 资源展示项) {
  return resource.type === 'folder' ? resource.item.name : resource.item.original_name
}

export function 获取资源时间(resource: 资源展示项) {
  return resource.type === 'folder' ? resource.item.updated_at : resource.item.created_at
}

export function 排序资源列表(
  folders: 文件夹展示项[],
  files: 文件展示项[],
  当前排序: 排序方式,
) {
  const sorted = [
    ...folders.map((folder) => ({ type: 'folder', id: folder.id, item: folder } as const)),
    ...files.map((file) => ({ type: 'file', id: file.id, item: file } as const)),
  ]
  sorted.sort((left, right) => {
    switch (当前排序) {
      case 'name-desc': {
        const result = 比较文本(获取资源名称(right), 获取资源名称(left))
        return result || 比较资源类型(left, right)
      }
      case 'time-desc': {
        const result = 比较时间(获取资源时间(right), 获取资源时间(left))
        return result || 比较资源类型(left, right) || 比较文本(获取资源名称(left), 获取资源名称(right))
      }
      case 'time-asc': {
        const result = 比较时间(获取资源时间(left), 获取资源时间(right))
        return result || 比较资源类型(left, right) || 比较文本(获取资源名称(left), 获取资源名称(right))
      }
      case 'size-desc':
      case 'size-asc': {
        if (left.type === 'folder' || right.type === 'folder') {
          return 比较资源类型(left, right) || 比较文本(获取资源名称(left), 获取资源名称(right))
        }
        const result = 当前排序 === 'size-desc'
          ? right.item.size - left.item.size
          : left.item.size - right.item.size
        return result || 比较文本(left.item.original_name, right.item.original_name)
      }
      default: {
        const result = 比较文本(获取资源名称(left), 获取资源名称(right))
        return result || 比较资源类型(left, right)
      }
    }
  })
  return sorted
}

export function 构建文件夹键(parentId: string | null, name: string) {
  return `${parentId ?? '__root__'}::${name.trim().toLowerCase()}`
}

export function 写入文件夹索引(nodes: FileTreeNode[], lookup: Map<string, string>) {
  for (const node of nodes) {
    lookup.set(构建文件夹键(node.parent_id, node.name), node.id)
    写入文件夹索引(node.children, lookup)
  }
}

export function 从目录树节点构建文件夹(node: FileTreeNode): FileFolderItem {
  return {
    id: node.id,
    parent_id: node.parent_id,
    name: node.name,
    created_at: '',
    updated_at: '',
  }
}

export function 收集目录树节点(node: FileTreeNode): FileTreeNode[] {
  return [node, ...node.children.flatMap((child) => 收集目录树节点(child))]
}

export function 插入新建目录节点(
  source: FileTreeNode[],
  draft: 新建目录草稿 | null,
): 目录树节点[] {
  if (!draft) {
    return source as 目录树节点[]
  }

  const draftNode: 目录树节点 = {
    id: draft.id,
    parent_id: draft.parentId,
    name: draft.name,
    isDraft: true,
    children: [],
  }

  if (draft.parentId === null) {
    return [...source, draftNode]
  }

  let inserted = false

  const visit = (nodes: FileTreeNode[]): 目录树节点[] => {
    let changed = false
    const nextNodes = nodes.map((node) => {
      if (node.id === draft.parentId) {
        inserted = true
        changed = true
        return {
          ...node,
          children: [...node.children, draftNode],
        }
      }

      if (!node.children.length) {
        return node as 目录树节点
      }

      const nextChildren = visit(node.children)
      if (nextChildren !== node.children) {
        changed = true
        return {
          ...node,
          children: nextChildren,
        }
      }

      return node as 目录树节点
    })

    return changed ? nextNodes : (nodes as 目录树节点[])
  }

  const nextTree = visit(source)
  return inserted ? nextTree : (source as 目录树节点[])
}
