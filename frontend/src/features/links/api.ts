import api from '../../utils/api'
import type {
  LinkAdminPayload,
  LinkExchangePayload,
  LinkExchangeResponse,
  LinkListResponse,
  LinkRecord,
  LinkStatus,
} from './types'

export async function fetchPublicLinks(): Promise<LinkRecord[]> {
  const { data } = await api.get<LinkRecord[]>('/links/public')
  return data
}

export async function requestLinkExchange(payload: LinkExchangePayload): Promise<LinkExchangeResponse> {
  const { data } = await api.post<LinkExchangeResponse>('/links/exchange', payload)
  return data
}

export async function fetchLinks(page: number, pageSize: number, status?: LinkStatus | ''): Promise<LinkListResponse> {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  }
  if (status) {
    params.status = status
  }
  const { data } = await api.get<LinkListResponse>('/links', { params })
  return data
}

export async function createLink(payload: LinkAdminPayload): Promise<LinkRecord> {
  const { data } = await api.post<LinkRecord>('/links', payload)
  return data
}

export async function updateLink(id: string, payload: LinkAdminPayload): Promise<LinkRecord> {
  const { data } = await api.patch<LinkRecord>(`/links/${id}`, payload)
  return data
}

export async function deleteLink(id: string): Promise<void> {
  await api.delete(`/links/${id}`)
}

export async function approveLink(id: string): Promise<void> {
  await api.post(`/links/${id}/approve`)
}

export async function rejectLink(id: string): Promise<void> {
  await api.post(`/links/${id}/reject`)
}
