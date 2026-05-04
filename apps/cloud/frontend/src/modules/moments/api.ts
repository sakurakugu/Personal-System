import api from '../../shared/api'
import type {
  MomentDraft,
  MomentImageRecord,
  MomentLikeResult,
  MomentListResponse,
  MomentPayload,
  MomentViewResult,
  PublishedMoment,
  UserMoment,
} from './types'

const DEFAULT_PAGE_SIZE = 10

export async function fetchPublishedMoments(page = 1, pageSize = DEFAULT_PAGE_SIZE): Promise<MomentListResponse<PublishedMoment>> {
  const { data } = await api.get<MomentListResponse<PublishedMoment>>('/moments', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function fetchMyMoments(page = 1, pageSize = DEFAULT_PAGE_SIZE): Promise<MomentListResponse<UserMoment>> {
  const { data } = await api.get<MomentListResponse<UserMoment>>('/moments/my/list', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function fetchMomentDraft(): Promise<MomentDraft | null> {
  const { data } = await api.get<MomentDraft | null>('/moments/draft')
  return data
}

export async function saveMomentDraft(payload: MomentPayload): Promise<MomentDraft> {
  const { data } = await api.put<MomentDraft>('/moments/draft', payload)
  return data
}

export async function fetchMomentImages(momentId: string): Promise<MomentImageRecord[]> {
  const { data } = await api.get<MomentImageRecord[]>(`/moments/${momentId}/images`)
  return data
}

export async function uploadMomentImage(momentId: string, file: File): Promise<MomentImageRecord> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<MomentImageRecord>(`/moments/${momentId}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function reorderMomentImages(momentId: string, imageIds: string[]): Promise<MomentImageRecord[]> {
  const { data } = await api.patch<MomentImageRecord[]>(`/moments/${momentId}/images/order`, {
    image_ids: imageIds,
  })
  return data
}

export async function deleteMomentImage(momentId: string, imageId: string): Promise<void> {
  await api.delete(`/moments/${momentId}/images/${imageId}`)
}

export async function publishMoment(payload: MomentPayload): Promise<UserMoment> {
  const { data } = await api.post<UserMoment>('/moments/publish', payload)
  return data
}

export async function fetchPublicMomentById(id: string): Promise<PublishedMoment> {
  const { data } = await api.get<PublishedMoment>(`/moments/public/${id}`)
  return data
}

export async function likeMoment(id: string): Promise<MomentLikeResult> {
  const { data } = await api.post<MomentLikeResult>(`/moments/${id}/like`)
  return data
}

export async function unlikeMoment(id: string): Promise<MomentLikeResult> {
  const { data } = await api.delete<MomentLikeResult>(`/moments/${id}/like`)
  return data
}

export async function recordMomentView(id: string): Promise<MomentViewResult> {
  const { data } = await api.post<MomentViewResult>(`/moments/${id}/view`)
  return data
}

export async function deleteMoment(id: string): Promise<void> {
  await api.delete(`/moments/${id}`)
}
