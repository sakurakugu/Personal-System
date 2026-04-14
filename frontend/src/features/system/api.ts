import api from '../../utils/api'
import type {
  AnnouncementRecord,
  BlogStats,
  DashboardStats,
  HealthCheckRead,
  PageViewPayload,
  PublicSettings,
} from './types'

export async function fetchPublicSettings(): Promise<PublicSettings> {
  const { data } = await api.get<PublicSettings>('/admin/public-settings')
  return data
}

export async function fetchBlogStats(): Promise<BlogStats> {
  const { data } = await api.get<BlogStats>('/stats/blog')
  return data
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/stats/dashboard')
  return data
}

export async function fetchHealthCheck(): Promise<HealthCheckRead> {
  const { data } = await api.get<HealthCheckRead>('/health', {
    validateStatus: (status) => status === 200 || status === 503,
  })
  return data
}

export async function fetchPublicAnnouncements(limit = 50): Promise<AnnouncementRecord[]> {
  const { data } = await api.get<AnnouncementRecord[]>('/announcements/public', {
    params: {
      limit,
    },
  })
  return data
}

export async function trackPageView(payload: PageViewPayload): Promise<void> {
  await api.post('/stats/pageview', payload)
}
