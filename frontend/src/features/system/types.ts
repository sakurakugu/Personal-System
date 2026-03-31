export interface PublicSettings {
  comments_enabled: boolean
  comments_stealth: boolean
  comments_min_role: string
  register_enabled: boolean
}

export const DEFAULT_PUBLIC_SETTINGS: PublicSettings = {
  comments_enabled: true,
  comments_stealth: false,
  comments_min_role: 'guest',
  register_enabled: true,
}

export interface RecentViewItem {
  date: string
  count: number
}

export interface DashboardStats {
  total_articles: number
  total_comments: number
  total_views: number
  total_todos: number
  current_month_bill_income_cent: number
  current_month_bill_expense_cent: number
  current_month_bill_net_cent: number
  current_month_bill_record_count: number
  recent_views: RecentViewItem[]
}

export interface AnnouncementRecord {
  id: string
  title: string
  content: string
  created_at: string
}

export interface HealthComponentStatus {
  status: string
  detail: string | null
}

export interface HealthCheckRead {
  status: string
  checked_at: string
  database: HealthComponentStatus
  redis: HealthComponentStatus
  minio: HealthComponentStatus
}

export interface PageViewPayload {
  path: string
  article_id?: string
}
