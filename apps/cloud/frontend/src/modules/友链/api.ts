import api from '../../shared/api'
import type {
  FriendLinkAdminPayload,
  FriendLinkListResponse,
  FriendLinkRecord,
  FriendLinkStatus,
} from './types'

export async function 获取公开友链(): Promise<FriendLinkRecord[]> {
  const { data } = await api.get<FriendLinkRecord[]>('/friend-links/public')
  return data
}

export async function 获取友链分类(): Promise<string[]> {
  const { data } = await api.get<string[]>('/friend-links/categories')
  return data
}

export async function 获取友链列表(
  page: number,
  pageSize: number,
  status?: FriendLinkStatus | '',
  isDeleted = false,
): Promise<FriendLinkListResponse> {
  const params: Record<string, string | number | boolean> = {
    page,
    page_size: pageSize,
    is_deleted: String(isDeleted),
  }
  if (status) {
    params.status = status
  }
  const { data } = await api.get<FriendLinkListResponse>('/friend-links', { params })
  return data
}

export async function 创建友链(payload: FriendLinkAdminPayload): Promise<FriendLinkRecord> {
  const { data } = await api.post<FriendLinkRecord>('/friend-links', payload)
  return data
}

export async function 更新友链(id: string, payload: FriendLinkAdminPayload): Promise<FriendLinkRecord> {
  const { data } = await api.patch<FriendLinkRecord>(`/friend-links/${id}`, payload)
  return data
}

export async function 删除友链(id: string, permanent = false): Promise<void> {
  await api.delete(`/friend-links/${id}`, { params: { permanent } })
}

export async function 恢复友链(id: string): Promise<FriendLinkRecord> {
  const { data } = await api.post<FriendLinkRecord>(`/friend-links/${id}/restore`)
  return data
}

export async function 批准友链(id: string): Promise<void> {
  await api.post(`/friend-links/${id}/approve`)
}

export async function 拒绝友链(id: string): Promise<void> {
  await api.post(`/friend-links/${id}/reject`)
}

