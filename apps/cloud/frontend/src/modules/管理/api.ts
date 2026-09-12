import api from '../../shared/api'
import type {
  AdminSettings,
  AICallLogListResponse,
  AISettings,
  AITestResponse,
  AnnouncementListResponse,
  AnnouncementPayload,
  AnnouncementRecord,
  MCPTokenCreatePayload,
  MCPTokenCreateResponse,
  SystemStatus,
  TwikooPasswordState,
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
  const { data } = await api.get<AdminSettings>('/system/settings')
  return data
}

export async function 更新管理设置(
  payload: Partial<Pick<AdminSettings, 'comments_enabled' | 'comments_hidden'>>,
): Promise<AdminSettings> {
  const { data } = await api.patch<AdminSettings>('/system/settings', payload)
  return data
}

export async function 获取系统状态(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>('/system/status')
  return data
}

export async function 获取Twikoo密码状态(): Promise<TwikooPasswordState> {
  const { data } = await api.get<TwikooPasswordState>('/system/twikoo/password')
  return data
}

export async function 获取AI设置(): Promise<AISettings> {
  const { data } = await api.get<AISettings>('/ai/settings')
  return data
}

export async function 更新AI设置(payload: Partial<AISettings>): Promise<AISettings> {
  const { data } = await api.patch<AISettings>('/ai/settings', payload)
  return data
}

export async function 更新AI密钥(secret: string): Promise<AISettings> {
  const { data } = await api.patch<AISettings>('/ai/secret', { secret })
  return data
}

export async function 测试AI配置(message: string): Promise<AITestResponse> {
  const { data } = await api.post<AITestResponse>('/ai/test', { message })
  return data
}

export async function 获取AI调用日志(page: number, pageSize: number): Promise<AICallLogListResponse> {
  const { data } = await api.get<AICallLogListResponse>('/ai/logs', {
    params: {
      page,
      page_size: pageSize,
    },
  })
  return data
}

export async function 创建MCP令牌(payload: MCPTokenCreatePayload): Promise<MCPTokenCreateResponse> {
  const { data } = await api.post<MCPTokenCreateResponse>('/auth/mcp/token', payload)
  return data
}

export async function 重置Twikoo密码(password: string): Promise<TwikooPasswordState> {
  const { data } = await api.post<TwikooPasswordState>('/system/twikoo/password/reset', { password })
  return data
}

