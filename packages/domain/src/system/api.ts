import api from '@personal-system/api'
import type {
  AnnouncementRecord,
  BlogStats,
  DashboardStats,
  HealthCheckRead,
  PageViewPayload,
  PublicSettings,
} from './types'

export async function 获取公开设置(): Promise<PublicSettings> {
  const { data } = await api.get<PublicSettings>('/admin/public-settings')
  return data
}

export async function 获取博客统计(): Promise<BlogStats> {
  const { data } = await api.get<BlogStats>('/stats/blog')
  return data
}

export async function 获取仪表盘统计(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/stats/dashboard')
  return data
}

export async function 获取健康检查(): Promise<HealthCheckRead> {
  const { data } = await api.get<HealthCheckRead>('/health', {
    validateStatus: (status: number) => status === 200 || status === 503,
  })
  return data
}

export async function 获取公开公告(limit = 50): Promise<AnnouncementRecord[]> {
  const { data } = await api.get<AnnouncementRecord[]>('/announcements/public', {
    params: {
      limit,
    },
  })
  return data
}

export async function 追踪页面访问(payload: PageViewPayload): Promise<void> {
  await api.post('/stats/pageview', payload)
}
