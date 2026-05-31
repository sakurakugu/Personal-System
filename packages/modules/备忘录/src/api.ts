import api from '@personal-system/api'
import type {
  MemoConvertResult,
  MemoCreatePayload,
  MemoListQuery,
  MemoListResponse,
  MemoRecord,
  MemoUpdatePayload,
} from './types'

export async function 获取备忘录列表(query: MemoListQuery = {}): Promise<MemoListResponse> {
  const params: Record<string, string | number> = {}
  if (query.page) params.page = query.page
  if (query.page_size) params.page_size = query.page_size
  if (query.status) params.status = query.status
  if (query.source) params.source = query.source
  if (query.keyword) params.keyword = query.keyword
  params.is_deleted = String(query.is_deleted ?? false)

  const { data } = await api.get<MemoListResponse>('/memos', { params })
  return data
}

export async function 创建备忘录(payload: MemoCreatePayload): Promise<MemoRecord> {
  const { data } = await api.post<MemoRecord>('/memos', payload)
  return data
}

export async function 更新备忘录(id: string, payload: MemoUpdatePayload): Promise<MemoRecord> {
  const { data } = await api.patch<MemoRecord>(`/memos/${id}`, payload)
  return data
}

export async function 删除备忘录(id: string, permanent = false): Promise<void> {
  await api.delete(`/memos/${id}`, {
    params: { permanent },
  })
}

export async function 恢复备忘录(id: string): Promise<MemoRecord> {
  const { data } = await api.post<MemoRecord>(`/memos/${id}/restore`)
  return data
}

export async function 转换备忘录为资料(id: string): Promise<MemoConvertResult> {
  const { data } = await api.post<MemoConvertResult>(`/memos/${id}/convert/collection`)
  return data
}

export async function 转换备忘录为文章(id: string): Promise<MemoConvertResult> {
  const { data } = await api.post<MemoConvertResult>(`/memos/${id}/convert/article`)
  return data
}

export async function 转换备忘录为待办(id: string): Promise<MemoConvertResult> {
  const { data } = await api.post<MemoConvertResult>(`/memos/${id}/convert/todo`)
  return data
}
