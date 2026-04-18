import api from '../../shared/api'
import type {
  AdminSettings,
  AnnouncementListResponse,
  AnnouncementPayload,
  AnnouncementRecord,
  PendingComment,
  SystemStatus,
  UserCreatePayload,
  UserItem,
  UserListQuery,
  UserListResponse,
  UserUpdatePayload,
} from './types'

export async function fetchPendingComments(): Promise<PendingComment[]> {
  const { data } = await api.get<PendingComment[]>('/comments/pending')
  return data
}

export async function moderateComment(id: string, status: 'approved' | 'rejected'): Promise<void> {
  await api.patch(`/comments/${id}/moderate`, { status })
}

export async function fetchAnnouncements(page: number, pageSize: number): Promise<AnnouncementListResponse> {
  const { data } = await api.get<AnnouncementListResponse>('/announcements', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function createAnnouncement(payload: AnnouncementPayload): Promise<AnnouncementRecord> {
  const { data } = await api.post<AnnouncementRecord>('/announcements', payload)
  return data
}

export async function updateAnnouncement(id: string, payload: AnnouncementPayload): Promise<AnnouncementRecord> {
  const { data } = await api.patch<AnnouncementRecord>(`/announcements/${id}`, payload)
  return data
}

export async function deleteAnnouncement(id: string): Promise<void> {
  await api.delete(`/announcements/${id}`)
}

export async function fetchAdminSettings(): Promise<AdminSettings> {
  const { data } = await api.get<AdminSettings>('/admin/settings')
  return data
}

export async function updateAdminSettings(
  payload: Partial<Pick<AdminSettings, 'comments_enabled' | 'comments_stealth' | 'comments_min_role' | 'register_enabled'>>,
): Promise<AdminSettings> {
  const { data } = await api.patch<AdminSettings>('/admin/settings', payload)
  return data
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>('/admin/system')
  return data
}

export async function fetchUsers(query: UserListQuery): Promise<UserListResponse> {
  const params: Record<string, string | number | boolean> = { ...query }
  const { data } = await api.get<UserListResponse>('/users', { params })
  return data
}

export async function createUser(payload: UserCreatePayload): Promise<UserItem> {
  const { data } = await api.post<UserItem>('/users', payload)
  return data
}

export async function updateUser(id: string, payload: UserUpdatePayload): Promise<UserItem> {
  const { data } = await api.patch<UserItem>(`/users/${id}`, payload)
  return data
}

export async function resetUserPassword(id: string, password: string): Promise<void> {
  await api.patch(`/users/${id}/password`, { password })
}

export async function deleteUser(id: string): Promise<void> {
  await api.delete(`/users/${id}`)
}

