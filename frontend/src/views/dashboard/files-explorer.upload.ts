import {
  createFolder as requestCreateFolder,
  uploadFile as requestUploadFile,
} from '../../features/files/api'
import { 写入文件夹索引, 构建文件夹键 } from './files-explorer.shared'
import type { FileTreeNode } from '../../features/files/types'
import type { 带目录路径文件 } from './files-explorer.shared'

export interface 上传执行结果 {
  成功数量: number
  失败原因: unknown[]
}

function 构建文件夹索引(source: FileTreeNode[]) {
  const lookup = new Map<string, string>()
  写入文件夹索引(source, lookup)
  return lookup
}

async function 确保目录路径(
  relativeDirectory: string,
  currentFolderId: string | null,
  lookup: Map<string, string>,
) {
  let parentId = currentFolderId
  const segments = relativeDirectory.split('/').map((item) => item.trim()).filter(Boolean)

  for (const segment of segments) {
    const folderKey = 构建文件夹键(parentId, segment)
    let folderId = lookup.get(folderKey) ?? null
    if (!folderId) {
      const createdFolder = await requestCreateFolder(segment, parentId)
      folderId = createdFolder.id
      lookup.set(folderKey, folderId)
    }
    parentId = folderId
  }

  return parentId
}

export async function 执行文件上传(files: globalThis.File[], currentFolderId: string | null): Promise<上传执行结果> {
  const results = await Promise.allSettled(files.map((file) => requestUploadFile(file, currentFolderId)))
  const 失败原因 = results
    .filter((result): result is PromiseRejectedResult => result.status === 'rejected')
    .map((result) => result.reason)

  return {
    成功数量: results.length - 失败原因.length,
    失败原因,
  }
}

export async function 执行目录上传(
  files: 带目录路径文件[],
  currentFolderId: string | null,
  tree: FileTreeNode[],
): Promise<上传执行结果> {
  const folderLookup = 构建文件夹索引(tree)
  let 成功数量 = 0
  const 失败原因: unknown[] = []

  for (const file of files) {
    try {
      const relativePath = (file.webkitRelativePath || file.name).replace(/\\/g, '/')
      const segments = relativePath.split('/').filter(Boolean)
      const directoryPath = segments.slice(0, -1).join('/')
      const folderId = await 确保目录路径(directoryPath, currentFolderId, folderLookup)
      await requestUploadFile(file, folderId)
      成功数量 += 1
    } catch (error) {
      失败原因.push(error)
    }
  }

  return {
    成功数量,
    失败原因,
  }
}
