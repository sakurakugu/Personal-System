import api from '../../utils/api'
import type {
  FriendLinkAdminPayload,
  FriendLinkListResponse,
  FriendLinkRecord,
  FriendLinkStatus,
} from './types'

export async function fetchPublicFriendLinks(): Promise<FriendLinkRecord[]> {
  const { data } = await api.get<FriendLinkRecord[]>('/friend-links/public')
  return data
}

export async function fetchFriendLinkCategories(): Promise<string[]> {
  const { data } = await api.get<string[]>('/friend-links/categories')
  return data
}

export async function fetchFriendLinks(
  page: number,
  pageSize: number,
  status?: FriendLinkStatus | '',
): Promise<FriendLinkListResponse> {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  }
  if (status) {
    params.status = status
  }
  const { data } = await api.get<FriendLinkListResponse>('/friend-links', { params })
  return data
}

export async function createFriendLink(payload: FriendLinkAdminPayload): Promise<FriendLinkRecord> {
  const { data } = await api.post<FriendLinkRecord>('/friend-links', payload)
  return data
}

export async function updateFriendLink(id: string, payload: FriendLinkAdminPayload): Promise<FriendLinkRecord> {
  const { data } = await api.patch<FriendLinkRecord>(`/friend-links/${id}`, payload)
  return data
}

export async function deleteFriendLink(id: string): Promise<void> {
  await api.delete(`/friend-links/${id}`)
}

export async function approveFriendLink(id: string): Promise<void> {
  await api.post(`/friend-links/${id}/approve`)
}

export async function rejectFriendLink(id: string): Promise<void> {
  await api.post(`/friend-links/${id}/reject`)
}
