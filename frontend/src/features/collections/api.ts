import api from '../../utils/api'
import type {
  CollectionBatchStatusPayload,
  CollectionConvertResult,
  CollectionListQuery,
  CollectionListResponse,
  CollectionPayload,
  CollectionRecord,
  CollectionTagStat,
} from './types'

export async function fetchCollections(query: CollectionListQuery = {}): Promise<CollectionListResponse> {
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

export async function fetchCollectionTags(isDeleted = false): Promise<CollectionTagStat[]> {
  const { data } = await api.get<CollectionTagStat[]>('/collections/tags', {
    params: { is_deleted: String(isDeleted) },
  })
  return data
}

export async function createCollection(payload: CollectionPayload): Promise<CollectionRecord> {
  const { data } = await api.post<CollectionRecord>('/collections', payload)
  return data
}

export async function updateCollection(id: string, payload: Partial<CollectionPayload>): Promise<CollectionRecord> {
  const { data } = await api.patch<CollectionRecord>(`/collections/${id}`, payload)
  return data
}

export async function deleteCollection(id: string, permanent = false): Promise<void> {
  await api.delete(`/collections/${id}?permanent=${String(permanent)}`)
}

export async function restoreCollection(id: string): Promise<CollectionRecord> {
  const { data } = await api.post<CollectionRecord>(`/collections/${id}/restore`)
  return data
}

export async function batchUpdateCollectionStatus(payload: CollectionBatchStatusPayload): Promise<number> {
  const { data } = await api.post<{ count: number }>('/collections/batch/status', payload)
  return data.count
}

export async function convertCollectionToArticle(id: string): Promise<CollectionConvertResult> {
  const { data } = await api.post<CollectionConvertResult>(`/collections/${id}/convert/article`)
  return data
}

export async function convertCollectionToMomentDraft(id: string): Promise<CollectionConvertResult> {
  const { data } = await api.post<CollectionConvertResult>(`/collections/${id}/convert/moment-draft`)
  return data
}

export async function convertCollectionToTodo(id: string): Promise<CollectionConvertResult> {
  const { data } = await api.post<CollectionConvertResult>(`/collections/${id}/convert/todo`)
  return data
}
