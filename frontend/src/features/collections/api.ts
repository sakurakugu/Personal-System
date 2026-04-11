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
  if (query.source_type) params.source_type = query.source_type
  if (query.type) params.type = query.type
  if (query.tag) params.tag = query.tag
  if (query.keyword) params.keyword = query.keyword

  const { data } = await api.get<CollectionListResponse>('/collections', { params })
  return data
}

export async function fetchCollectionTags(): Promise<CollectionTagStat[]> {
  const { data } = await api.get<CollectionTagStat[]>('/collections/tags')
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

export async function deleteCollection(id: string): Promise<void> {
  await api.delete(`/collections/${id}`)
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
