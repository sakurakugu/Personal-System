import api from '@personal-system/api'

export async function deleteFile(id: string): Promise<void> {
  await api.delete(`/files/${id}`)
}
