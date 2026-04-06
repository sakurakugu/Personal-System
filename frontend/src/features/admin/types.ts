import type { HealthCheckRead, PublicSettings } from '../system/types'

export interface PendingComment {
  id: string
  article_id: string
  article: { id: string; title: string; slug: string } | null
  content: string
  guest_name: string | null
  user: { username: string; nickname: string | null } | null
  created_at: string
}

export interface AnnouncementRecord {
  id: string
  title: string
  content: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AnnouncementListResponse {
  items: AnnouncementRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AnnouncementPayload {
  title: string
  content: string
  is_active: boolean
}

export type AdminSettings = PublicSettings

export interface SystemRequestEvent {
  method: string
  path: string
  status_code: number
  duration_ms: number
  happened_at: string
  detail: string | null
}

export interface SystemRequestAggregate {
  method: string
  path: string
  count: number
  last_status_code: number
  last_happened_at: string
  max_duration_ms: number
  avg_duration_ms: number
  detail: string | null
}

export interface SystemRuntimeSnapshot {
  recent_window_minutes: number
  slow_request_threshold_ms: number
  error_count: number
  slow_request_count: number
  top_error_routes: SystemRequestAggregate[]
  top_slow_routes: SystemRequestAggregate[]
  recent_errors: SystemRequestEvent[]
  recent_slow_requests: SystemRequestEvent[]
}

export interface SystemStatus {
  cpu_percent: number
  memory_total_gb: number
  memory_used_gb: number
  memory_percent: number
  disk_total_gb: number
  disk_used_gb: number
  disk_percent: number
  uptime_seconds: number
  health: HealthCheckRead
  runtime: SystemRuntimeSnapshot
}

export type UserRole = 'user' | 'admin' | 'super_admin'

export interface UserSettings {
  show_private_articles_on_home: boolean
}

export interface UserItem {
  id: string
  username: string
  nickname: string | null
  email: string
  role: UserRole
  avatar_url: string | null
  bio: string | null
  settings: UserSettings
  is_active: boolean
  created_at: string
}

export interface UserListResponse {
  items: UserItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface UserListQuery {
  page: number
  page_size: number
  keyword?: string
  role?: string
  is_active?: boolean
}

export interface UserCreatePayload {
  username: string
  nickname: string | null
  email: string
  password: string
  role: UserRole
  is_active: boolean
  bio: string | null
  avatar_url: string | null
}

export interface UserUpdatePayload {
  username: string
  nickname: string | null
  email: string
  role: UserRole
  is_active: boolean
  bio: string | null
  avatar_url: string | null
}
