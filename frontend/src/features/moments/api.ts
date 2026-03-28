import api from '../../utils/api'
import type {
  MomentDraft,
  MomentListResponse,
  MomentPayload,
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

export async function publishMoment(payload: MomentPayload): Promise<UserMoment> {
  const { data } = await api.post<UserMoment>('/moments/publish', payload)
  return data
}

export async function deleteMoment(id: string): Promise<void> {
  await api.delete(`/moments/${id}`)
}
