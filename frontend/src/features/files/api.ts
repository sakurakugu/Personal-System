import api from '../../utils/api'
import type { FileItem } from './types'

export async function fetchFiles(): Promise<FileItem[]> {
  const { data } = await api.get<FileItem[]>('/files')
  return data
}

export async function uploadFile(file: File): Promise<FileItem> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<FileItem>('/files', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function deleteFile(id: string): Promise<void> {
  await api.delete(`/files/${id}`)
}
