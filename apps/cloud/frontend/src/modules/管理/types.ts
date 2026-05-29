import type { HealthCheckRead, PublicSettings } from '../../modules/系统/types'

export interface AnnouncementRecord {
  id: string
  title: string
  content: string
  is_active: boolean
  is_deleted: boolean
  deleted_at: string | null
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

export interface TwikooPasswordState {
  available: boolean
  detail: string
  last_reset_password: string | null
  last_reset_at: string | null
}

export type AIAccessPolicy = 'login' | 'admin' | 'super_admin'

export interface AISettings {
  enabled: boolean
  access_policy: AIAccessPolicy
  provider: string
  base_url: string
  model: string
  max_tokens: number
  timeout_seconds: number
  system_prompt: string
  allow_attachments: boolean
  max_attachment_size_mb: number
  daily_limit_per_user: number
  has_secret: boolean
  secret_updated_at: string | null
  updated_at: string | null
}

export interface AICallLog {
  id: string
  user_id: string | null
  provider: string
  model: string
  status: string
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  duration_ms: number
  message_count: number
  attachment_count: number
  error_type: string | null
  error_message: string | null
  created_at: string
}

export interface AICallLogListResponse {
  items: AICallLog[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface AITestResponse {
  content: string
  duration_ms: number
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
