import api from '@personal-system/api'
import type {
  ExternalCoverImportPayload,
  ExternalMediaCandidate,
  ExternalMediaImportPayload,
  ExternalMediaSearchResponse,
  MediaAsset,
  MediaCreatorSuggestion,
  MediaFilterStat,
  MediaListQuery,
  MediaListResponse,
  MediaPayload,
  MediaRecord,
} from './types'

function 构建列表参数(query: MediaListQuery = {}) {
  const params: Record<string, string | number | boolean> = {}
  if (query.page) params.page = query.page
  if (query.page_size) params.page_size = query.page_size
  if (query.media_type) params.media_type = query.media_type
  if (query.status) params.status = query.status
  if (typeof query.rating === 'number') params.rating = query.rating
  if (query.keyword) params.keyword = query.keyword
  if (query.genre) params.genre = query.genre
  if (query.tag) params.tag = query.tag
  if (query.personal_tag) params.personal_tag = query.personal_tag
  if (query.is_deleted !== undefined) params.is_deleted = query.is_deleted
  return params
}

export async function 获取文娱列表(query: MediaListQuery = {}): Promise<MediaListResponse> {
  const { data } = await api.get<MediaListResponse>('/media', { params: 构建列表参数(query) })
  return data
}

export async function 获取公开文娱列表(query: MediaListQuery = {}): Promise<MediaListResponse> {
  const { data } = await api.get<MediaListResponse>('/media/public', { params: 构建列表参数(query) })
  return data
}

export async function 获取文娱详情(id: string): Promise<MediaRecord> {
  const { data } = await api.get<MediaRecord>(`/media/${id}`)
  return data
}

export async function 获取公开文娱详情(id: string): Promise<MediaRecord> {
  const { data } = await api.get<MediaRecord>(`/media/public/${id}`)
  return data
}

export async function 创建文娱(payload: MediaPayload): Promise<MediaRecord> {
  const { data } = await api.post<MediaRecord>('/media', payload)
  return data
}

export async function 更新文娱(id: string, payload: Partial<MediaPayload>): Promise<MediaRecord> {
  const { data } = await api.patch<MediaRecord>(`/media/${id}`, payload)
  return data
}

export async function 删除文娱(id: string, permanent = false): Promise<void> {
  await api.delete(`/media/${id}`, { params: { permanent } })
}

export async function 恢复文娱(id: string): Promise<MediaRecord> {
  const { data } = await api.post<MediaRecord>(`/media/${id}/restore`)
  return data
}

export async function 获取文娱类型统计(): Promise<MediaFilterStat[]> {
  const { data } = await api.get<MediaFilterStat[]>('/media/types')
  return data
}

export async function 获取文娱子分类统计(mediaType?: string): Promise<MediaFilterStat[]> {
  const params: Record<string, string> = {}
  if (mediaType) {
    params.media_type = mediaType
  }
  const { data } = await api.get<MediaFilterStat[]>('/media/genres', { params })
  return data
}

export async function 获取文娱标签统计(mediaType?: string): Promise<MediaFilterStat[]> {
  const params: Record<string, string> = {}
  if (mediaType) {
    params.media_type = mediaType
  }
  const { data } = await api.get<MediaFilterStat[]>('/media/tags', { params })
  return data
}

export async function 获取文娱个人标签统计(mediaType?: string): Promise<MediaFilterStat[]> {
  const params: Record<string, string> = {}
  if (mediaType) {
    params.media_type = mediaType
  }
  const { data } = await api.get<MediaFilterStat[]>('/media/personal-tags', { params })
  return data
}

export async function 获取文娱创作者建议(keyword?: string, limit = 10): Promise<MediaCreatorSuggestion[]> {
  const params: Record<string, string | number> = { limit }
  if (keyword?.trim()) {
    params.keyword = keyword.trim()
  }
  const { data } = await api.get<MediaCreatorSuggestion[]>('/media/creators', { params })
  return data
}

export async function 搜索外部文娱(
  keyword: string,
  mediaType?: MediaListQuery['media_type'],
  provider?: string,
): Promise<ExternalMediaSearchResponse> {
  const params: Record<string, string> = { keyword }
  if (mediaType) params.media_type = mediaType
  if (provider) params.provider = provider
  const { data } = await api.get<ExternalMediaSearchResponse>('/media/external/search', { params })
  return data
}

export async function 获取外部文娱详情(provider: string, externalId: string): Promise<ExternalMediaCandidate> {
  const { data } = await api.get<ExternalMediaCandidate>(`/media/external/${provider}/${externalId}`)
  return data
}

export async function 从外部导入文娱(payload: ExternalMediaImportPayload): Promise<MediaRecord> {
  const { data } = await api.post<MediaRecord>('/media/import', payload)
  return data
}

export async function 从外部URL导入封面(
  mediaId: string,
  payload: ExternalCoverImportPayload,
  localize = true,
): Promise<MediaAsset> {
  const { data } = await api.post<MediaAsset>(`/media/${mediaId}/assets/import-cover`, payload, {
    params: { localize },
  })
  return data
}

export async function 上传文娱封面(mediaId: string, file: File): Promise<MediaAsset> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<MediaAsset>(`/media/${mediaId}/assets/upload-cover`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}
