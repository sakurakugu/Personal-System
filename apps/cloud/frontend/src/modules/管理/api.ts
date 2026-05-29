import api from '../../shared/api'
import type {
  AdminSettings,
  AICallLogListResponse,
  AISettings,
  AITestResponse,
  AnnouncementListResponse,
  AnnouncementPayload,
  AnnouncementRecord,
  SystemStatus,
  TwikooPasswordState,
  UserCreatePayload,
  UserItem,
  UserListQuery,
  UserListResponse,
  UserUpdatePayload,
} from './types'

export async function 获取公告列表(page: number, pageSize: number, isDeleted = false): Promise<AnnouncementListResponse> {
  const { data } = await api.get<AnnouncementListResponse>('/announcements', {
    params: {
      page,
      page_size: pageSize,
      is_deleted: isDeleted,
    },
  })
  return data
}

export async function 创建公告(payload: AnnouncementPayload): Promise<AnnouncementRecord> {
  const { data } = await api.post<AnnouncementRecord>('/announcements', payload)
  return data
}

export async function 更新公告(id: string, payload: AnnouncementPayload): Promise<AnnouncementRecord> {
  const { data } = await api.patch<AnnouncementRecord>(`/announcements/${id}`, payload)
  return data
}

export async function 删除公告(id: string, permanent = false): Promise<void> {
  await api.delete(`/announcements/${id}`, { params: { permanent } })
}

export async function 恢复公告(id: string): Promise<AnnouncementRecord> {
  const { data } = await api.post<AnnouncementRecord>(`/announcements/${id}/restore`)
  return data
}

export async function 获取管理设置(): Promise<AdminSettings> {
  const { data } = await api.get<AdminSettings>('/admin/settings')
  return data
}

export async function 更新管理设置(
  payload: Partial<Pick<AdminSettings, 'register_enabled' | 'comments_enabled' | 'comments_hidden'>>,
): Promise<AdminSettings> {
  const { data } = await api.patch<AdminSettings>('/admin/settings', payload)
  return data
}

export async function 获取系统状态(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>('/admin/system')
  return data
}

export async function 获取Twikoo密码状态(): Promise<TwikooPasswordState> {
  const { data } = await api.get<TwikooPasswordState>('/admin/twikoo/password')
  return data
}

export async function 获取AI设置(): Promise<AISettings> {
  const { data } = await api.get<AISettings>('/admin/ai/settings')
  return data
}

export async function 更新AI设置(payload: Partial<AISettings>): Promise<AISettings> {
  const { data } = await api.patch<AISettings>('/admin/ai/settings', payload)
  return data
}

export async function 更新AI密钥(secret: string): Promise<AISettings> {
  const { data } = await api.patch<AISettings>('/admin/ai/secret', { secret })
  return data
}

export async function 测试AI配置(message: string): Promise<AITestResponse> {
  const { data } = await api.post<AITestResponse>('/admin/ai/test', { message })
  return data
}

export async function 获取AI调用日志(page: number, pageSize: number): Promise<AICallLogListResponse> {
  const { data } = await api.get<AICallLogListResponse>('/admin/ai/logs', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function 重置Twikoo密码(password: string): Promise<TwikooPasswordState> {
  const { data } = await api.post<TwikooPasswordState>('/admin/twikoo/password/reset', { password })
  return data
}

export async function 获取用户列表(query: UserListQuery): Promise<UserListResponse> {
  const params: Record<string, string | number | boolean> = { ...query }
  const { data } = await api.get<UserListResponse>('/users', { params })
  return data
}

export async function 创建用户(payload: UserCreatePayload): Promise<UserItem> {
  const { data } = await api.post<UserItem>('/users', payload)
  return data
}

export async function 更新用户(id: string, payload: UserUpdatePayload): Promise<UserItem> {
  const { data } = await api.patch<UserItem>(`/users/${id}`, payload)
  return data
}

export async function 重置用户密码(id: string, password: string): Promise<void> {
  await api.patch(`/users/${id}/password`, { password })
}

export async function 删除用户(id: string): Promise<void> {
  await api.delete(`/users/${id}`)
}

