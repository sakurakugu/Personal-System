import api from '@personal-system/api'
import type {
  CollectionBatchStatusPayload,
  CollectionConvertResult,
  CollectionListQuery,
  CollectionListResponse,
  CollectionPayload,
  CollectionRecord,
  CollectionTagStat,
} from './types'

export async function 获取收藏列表(query: CollectionListQuery = {}): Promise<CollectionListResponse> {
  const params: Record<string, string | number> = {}
  if (query.page) params.page = query.page
  if (query.page_size) params.page_size = query.page_size
  if (query.status) params.status = query.status
  if (query.type) params.type = query.type
  if (query.tag) params.tag = query.tag
  if (query.keyword) params.keyword = query.keyword
  params.is_deleted = String(query.is_deleted ?? false)

  const { data } = await api.get<CollectionListResponse>('/collections', { params })
  return data
}

export async function 获取收藏标签(isDeleted = false): Promise<CollectionTagStat[]> {
  const { data } = await api.get<CollectionTagStat[]>('/collections/tags', {
    params: { is_deleted: String(isDeleted) },
  })
  return data
}

export async function 创建收藏(payload: CollectionPayload): Promise<CollectionRecord> {
  const { data } = await api.post<CollectionRecord>('/collections', payload)
  return data
}

export async function 更新收藏(id: string, payload: Partial<CollectionPayload>): Promise<CollectionRecord> {
  const { data } = await api.patch<CollectionRecord>(`/collections/${id}`, payload)
  return data
}

export async function 删除收藏(id: string, permanent = false): Promise<void> {
  await api.delete(`/collections/${id}?permanent=${String(permanent)}`)
}

export async function 恢复收藏(id: string): Promise<CollectionRecord> {
  const { data } = await api.post<CollectionRecord>(`/collections/${id}/restore`)
  return data
}

export async function 批量更新收藏状态(payload: CollectionBatchStatusPayload): Promise<number> {
  const { data } = await api.post<{ count: number }>('/collections/batch/status', payload)
  return data.count
}

export async function 转换收藏为文章(id: string): Promise<CollectionConvertResult> {
  const { data } = await api.post<CollectionConvertResult>(`/collections/${id}/convert/article`)
  return data
}

export async function 转换收藏为动态草稿(id: string): Promise<CollectionConvertResult> {
  const { data } = await api.post<CollectionConvertResult>(`/collections/${id}/convert/moment-draft`)
  return data
}

export async function 转换收藏为待办(id: string): Promise<CollectionConvertResult> {
  const { data } = await api.post<CollectionConvertResult>(`/collections/${id}/convert/todo`)
  return data
}

