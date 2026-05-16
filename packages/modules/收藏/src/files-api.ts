import axios from 'axios'
import api, { 解析当前API基地址 } from '@personal-system/api'
import { 解析管理文件URL地址 } from './managedFile'
import type { FileExplorerData, FileFolderItem, FileItem, FileSearchData } from './files-types'

export async function 获取文件浏览器数据(folderId?: string | null): Promise<FileExplorerData> {
  const { data } = await api.get<FileExplorerData>('/files/explorer', {
    params: folderId ? { folder_id: folderId } : undefined,
  })
  return data
}

export async function 搜索文件(keyword: string): Promise<FileSearchData> {
  const { data } = await api.get<FileSearchData>('/files/search', {
    params: { keyword },
  })
  return data
}

export async function 上传文件(file: File, folderId?: string | null): Promise<FileItem> {
  const formData = new FormData()
  formData.append('file', file)
  if (folderId) {
    formData.append('folder_id', folderId)
  }
  const { data } = await api.post<FileItem>('/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function 创建文件夹(name: string, parentId?: string | null): Promise<FileFolderItem> {
  const { data } = await api.post<FileFolderItem>('/files/folders', {
    name,
    parent_id: parentId ?? null,
  })
  return data
}

export async function 重命名文件夹(id: string, name: string): Promise<FileFolderItem> {
  const { data } = await api.patch<FileFolderItem>(`/files/folders/${id}/rename`, { name })
  return data
}

export async function 移动文件夹(id: string, parentId?: string | null): Promise<FileFolderItem> {
  const { data } = await api.patch<FileFolderItem>(`/files/folders/${id}/move`, {
    parent_id: parentId ?? null,
  })
  return data
}

export async function 删除文件夹(id: string): Promise<void> {
  await api.delete(`/files/folders/${id}`)
}

export async function 移动文件(id: string, folderId?: string | null): Promise<FileItem> {
  const { data } = await api.patch<FileItem>(`/files/${id}/move`, {
    folder_id: folderId ?? null,
  })
  return data
}

export async function 重命名文件(id: string, originalName: string): Promise<FileItem> {
  const { data } = await api.patch<FileItem>(`/files/${id}/rename`, {
    original_name: originalName,
  })
  return data
}

export async function 删除文件(id: string): Promise<void> {
  await api.delete(`/files/${id}`)
}

function 解析文件下载URL(url: string): string {
  const resolvedManagedUrl = 解析管理文件URL地址(url)
  if (/^https?:\/\//.test(resolvedManagedUrl)) {
    return resolvedManagedUrl
  }

  const apiBase = 解析当前API基地址()

  if (/^https?:\/\//.test(apiBase)) {
    return new URL(resolvedManagedUrl, apiBase).toString()
  }

  return new URL(resolvedManagedUrl, globalThis.window.location.origin).toString()
}

export async function 下载文件(url: string): Promise<Blob> {
  const { data } = await axios.get(解析文件下载URL(url), {
    responseType: 'blob',
    withCredentials: true,
  })
  return data as Blob
}

export async function 下载归档(
  folderIds: string[],
  fileIds: string[],
  archiveName?: string,
): Promise<Blob> {
  const { data } = await api.post('/files/archive/download', {
    folder_ids: folderIds,
    file_ids: fileIds,
    archive_name: archiveName || null,
  }, {
    responseType: 'blob',
  })
  return data as Blob
}

