import api from '@personal-system/api'
import type {
  MaterialBatchStatusPayload,
  MaterialListQuery,
  MaterialListResponse,
  MaterialPayload,
  MaterialRecord,
  MaterialTagStat,
} from './types'

export async function 获取资料列表(query: MaterialListQuery = {}): Promise<MaterialListResponse> {
  const params: Record<string, string | number> = {}
  if (query.page) params.page = query.page
  if (query.page_size) params.page_size = query.page_size
  if (query.status) params.status = query.status
  if (query.type) params.type = query.type
  if (query.tag) params.tag = query.tag
  if (query.keyword) params.keyword = query.keyword
  params.is_deleted = String(query.is_deleted ?? false)

  const { data } = await api.get<MaterialListResponse>('/materials', { params })
  return data
}

export async function 获取资料标签(isDeleted = false): Promise<MaterialTagStat[]> {
  const { data } = await api.get<MaterialTagStat[]>('/materials/tags', {
    params: { is_deleted: String(isDeleted) },
  })
  return data
}

export async function 创建资料(payload: MaterialPayload): Promise<MaterialRecord> {
  const { data } = await api.post<MaterialRecord>('/materials', payload)
  return data
}

export async function 更新资料(id: string, payload: Partial<MaterialPayload>): Promise<MaterialRecord> {
  const { data } = await api.patch<MaterialRecord>(`/materials/${id}`, payload)
  return data
}

export async function 删除资料(id: string, permanent = false): Promise<void> {
  await api.delete(`/materials/${id}`, {
    params: {
      permanent,
    },
  })
}

export async function 恢复资料(id: string): Promise<MaterialRecord> {
  const { data } = await api.post<MaterialRecord>(`/materials/${id}/restore`)
  return data
}

export async function 批量更新资料状态(payload: MaterialBatchStatusPayload): Promise<number> {
  const { data } = await api.post<{ count: number }>('/materials/batch/status', payload)
  return data.count
}
