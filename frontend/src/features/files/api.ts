import api from '../../utils/api'
import type { FileExplorerData, FileFolderItem, FileItem, FileSearchData } from './types'

export async function fetchExplorer(folderId?: string | null): Promise<FileExplorerData> {
  const { data } = await api.get<FileExplorerData>('/files/explorer', {
    params: folderId ? { folder_id: folderId } : undefined,
  })
  return data
}

export async function searchFiles(keyword: string): Promise<FileSearchData> {
  const { data } = await api.get<FileSearchData>('/files/search', {
    params: { keyword },
  })
  return data
}

export async function uploadFile(file: File, folderId?: string | null): Promise<FileItem> {
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

export async function createFolder(name: string, parentId?: string | null): Promise<FileFolderItem> {
  const { data } = await api.post<FileFolderItem>('/files/folders', {
    name,
    parent_id: parentId ?? null,
  })
  return data
}

export async function renameFolder(id: string, name: string): Promise<FileFolderItem> {
  const { data } = await api.patch<FileFolderItem>(`/files/folders/${id}/rename`, { name })
  return data
}

export async function moveFolder(id: string, parentId?: string | null): Promise<FileFolderItem> {
  const { data } = await api.patch<FileFolderItem>(`/files/folders/${id}/move`, {
    parent_id: parentId ?? null,
  })
  return data
}

export async function deleteFolder(id: string): Promise<void> {
  await api.delete(`/files/folders/${id}`)
}

export async function moveFile(id: string, folderId?: string | null): Promise<FileItem> {
  const { data } = await api.patch<FileItem>(`/files/${id}/move`, {
    folder_id: folderId ?? null,
  })
  return data
}

export async function renameFile(id: string, originalName: string): Promise<FileItem> {
  const { data } = await api.patch<FileItem>(`/files/${id}/rename`, {
    original_name: originalName,
  })
  return data
}

export async function deleteFile(id: string): Promise<void> {
  await api.delete(`/files/${id}`)
}

export async function downloadArchive(
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
