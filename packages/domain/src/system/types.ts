export interface PublicSettings {
  register_enabled: boolean
  comments_enabled: boolean
  comments_hidden: boolean
}

export const DEFAULT_PUBLIC_SETTINGS: PublicSettings = {
  register_enabled: false,
  comments_enabled: false,
  comments_hidden: true,
}

export type CommentVisibilityMode = 'enabled' | 'closed' | 'hidden'

export interface RecentViewItem {
  date: string
  count: number
}

export interface BlogStats {
  total_articles: number
  total_categories: number
  total_tags: number
  total_words: number
  last_published_at: string | null
}

export interface DashboardStats {
  total_articles: number
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
