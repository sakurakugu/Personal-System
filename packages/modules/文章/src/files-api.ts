import api from '@personal-system/api'

export async function 删除文件(id: string): Promise<void> {
  await api.delete(`/files/${id}`)
}
