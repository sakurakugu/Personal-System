import type { FileFolderItem, FileItem } from '../types'
import { 提取扩展名 } from './files-explorer.resource'
import { 排序文件列表, 排序文件夹列表 } from './files-explorer.shared'
import type { 排序方式, 文件夹展示项, 文件展示项, 资源标识 } from './files-explorer.shared'

export interface 批量重命名配置 {
  前缀: string
  起始序号: number
  位数: number
  保留扩展名: boolean
}

export function 是否资源已选中(source: ReadonlySet<string>, id: string) {
  return source.has(id)
}

export function 更新选中集合(source: ReadonlySet<string>, id: string, selected: boolean) {
  const next = new Set(source)
  if (selected) {
    next.add(id)
  } else {
    next.delete(id)
  }
  return next
}

export function 切换当前页资源全选(
  已选文件夹: ReadonlySet<string>,
  已选文件: ReadonlySet<string>,
  当前展示文件夹列表: 文件夹展示项[],
  当前展示文件列表: 文件展示项[],
  是否已全选当前页: boolean,
) {
  const nextFolders = new Set(已选文件夹)
  const nextFiles = new Set(已选文件)

  for (const folder of 当前展示文件夹列表) {
    if (是否已全选当前页) {
      nextFolders.delete(folder.id)
    } else {
      nextFolders.add(folder.id)
    }
  }

  for (const file of 当前展示文件列表) {
    if (是否已全选当前页) {
      nextFiles.delete(file.id)
    } else {
      nextFiles.add(file.id)
    }
  }

  return {
    文件夹: nextFolders,
    文件: nextFiles,
  }
}

export function 读取当前已选资源(已选文件夹: ReadonlySet<string>, 已选文件: ReadonlySet<string>) {
  const selectedFolders = [...已选文件夹].map((id) => ({ type: 'folder', id } as const))
  const selectedFiles = [...已选文件].map((id) => ({ type: 'file', id } as const))
  return [...selectedFolders, ...selectedFiles]
}

export function 获取操作资源列表(resource: 资源标识 | undefined, 已选资源列表: 资源标识[]) {
  return resource ? [resource] : 已选资源列表
}

export function 生成批量序号(offset: number, 起始序号: number, 位数: number) {
  return String(起始序号 + offset).padStart(位数, '0')
}

export function 构建批量文件名(
  resource: 资源标识,
  offset: number,
  原始文件列表: FileItem[],
  配置: 批量重命名配置,
) {
  const serial = 生成批量序号(offset, 配置.起始序号, 配置.位数)
  if (resource.type === 'folder') {
    return `${配置.前缀}${serial}`
  }

  const file = 原始文件列表.find((item) => item.id === resource.id)
  const extension = file ? 提取扩展名(file.original_name) : ''
  if (!配置.保留扩展名 || !extension) {
    return `${配置.前缀}${serial}`
  }
  return `${配置.前缀}${serial}.${extension}`
}

export function 获取批量重命名资源列表(
  原始子文件夹列表: FileFolderItem[],
  原始文件列表: FileItem[],
  已选文件夹: ReadonlySet<string>,
  已选文件: ReadonlySet<string>,
  当前排序: 排序方式,
) {
  const orderedFolders = 排序文件夹列表(
    原始子文件夹列表.filter((folder) => 已选文件夹.has(folder.id)),
    当前排序,
  ).map((folder) => ({ type: 'folder', id: folder.id } as const))
  const orderedFiles = 排序文件列表(
    原始文件列表.filter((file) => 已选文件.has(file.id)),
    当前排序,
  ).map((file) => ({ type: 'file', id: file.id } as const))
  return [...orderedFolders, ...orderedFiles]
}
