import api from '@personal-system/api'

export interface WidgetSummaryItem {
  id: string
  title: string
  is_pinned: boolean
  importance: number
  urgency: number
  end_date: string | null
}

export interface PublicWidgetSummary {
  pending_count: number
  pinned_count: number
  overdue_count: number
  due_today_count: number
  items: WidgetSummaryItem[]
}

/** 未登录时读取小工具公开摘要（只读）。 */
export async function 获取公开小工具摘要(): Promise<PublicWidgetSummary> {
  const { data } = await api.get<PublicWidgetSummary>('/widget/summary', {
    params: {
      limit: 5,
    },
  })
  return data
}
