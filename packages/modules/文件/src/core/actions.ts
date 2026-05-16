import {
  创建文件夹 as requestCreateFolder,
  删除文件 as requestDeleteFile,
  删除文件夹 as requestDeleteFolder,
  移动文件 as requestMoveFile,
  移动文件夹 as requestMoveFolder,
  重命名文件 as requestRenameFile,
  重命名文件夹 as requestRenameFolder,
} from '../api'
import { 拆分资源列表, 汇总批量操作结果 } from './operations'
import type { 资源标识 } from './shared'

export interface 批量删除执行结果 {
  失败结果: PromiseRejectedResult[]
  成功数量: number
  当前目录已删除: boolean
}

export interface 批量执行结果 {
  失败结果: PromiseRejectedResult[]
  成功数量: number
}

export async function 执行文件夹创建(name: string, parentId: string | null) {
  return requestCreateFolder(name, parentId)
}

export async function 执行资源重命名(resource: 资源标识, name: string) {
  if (resource.type === 'folder') {
    return requestRenameFolder(resource.id, name)
  }
  return requestRenameFile(resource.id, name)
}

export async function 执行文件夹删除(folderId: string) {
  return requestDeleteFolder(folderId)
}

export async function 执行资源移动(resource: 资源标识, targetFolderId: string | null) {
  if (resource.type === 'file') {
    return requestMoveFile(resource.id, targetFolderId)
  }
  return requestMoveFolder(resource.id, targetFolderId)
}

export async function 执行批量删除资源(
  targetResources: 资源标识[],
  currentFolderId: string | null,
): Promise<批量删除执行结果> {
  const groupedResources = 拆分资源列表(targetResources)
  const 当前目录删除结果索引 = currentFolderId
    ? groupedResources.文件夹.findIndex((item) => item.id === currentFolderId)
    : -1
  const 文件删除结果 = await Promise.allSettled(groupedResources.文件.map((item) => requestDeleteFile(item.id)))
  const 文件夹删除结果 = await Promise.allSettled(groupedResources.文件夹.map((item) => requestDeleteFolder(item.id)))
  const 结果汇总 = 汇总批量操作结果([
    ...文件删除结果,
    ...文件夹删除结果,
  ])

  return {
    ...结果汇总,
    当前目录已删除: 当前目录删除结果索引 >= 0 && 文件夹删除结果[当前目录删除结果索引]?.status === 'fulfilled',
  }
}

export async function 执行批量重命名资源(
  targetResources: 资源标识[],
  nameBuilder: (resource: 资源标识, index: number) => string,
): Promise<批量执行结果> {
  const results = await Promise.allSettled(
    targetResources.map((resource, index) => 执行资源重命名(resource, nameBuilder(resource, index))),
  )
  return 汇总批量操作结果(results)
}

export async function 执行批量移动资源(
  targetResources: 资源标识[],
  targetFolderId: string | null,
): Promise<批量执行结果> {
  const groupedResources = 拆分资源列表(targetResources)
  const results = [
    ...(await Promise.allSettled(groupedResources.文件.map((item) => requestMoveFile(item.id, targetFolderId)))),
    ...(await Promise.allSettled(groupedResources.文件夹.map((item) => requestMoveFolder(item.id, targetFolderId)))),
  ]
  return 汇总批量操作结果(results)
}
