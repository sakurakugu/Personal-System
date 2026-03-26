import { computed } from 'vue'
import { useThemeStore } from '../stores/theme'
import type { Todo } from '../stores/todo'

// ============ 标签相关 ============

export function parseTags(tags: string[] | null): string[] {
  if (!tags) return []
  return tags.map(tag => tag.trim()).filter(Boolean)
}

// ============ 优先级相关 ============

export function getPriorityTagType(value: number): 'success' | 'info' | 'warning' | 'danger' {
  if (value >= 86) return 'danger'
  if (value >= 67) return 'warning'
  if (value >= 33) return 'success'
  return 'info'
}

export function getPriorityLabel(value: number): string {
  if (value >= 86) return '非常重要'
  if (value >= 67) return '重要'
  if (value >= 33) return '一般'
  return '不重要'
}

// ============ 日期相关 ============

export function isNearDeadline(endDate: string | null): boolean {
  if (!endDate) return false
  const end = new Date(endDate)
  const now = new Date()
  const diff = end.getTime() - now.getTime()
  return diff > 0 && diff < 24 * 60 * 60 * 1000
}

export function isOverdue(endDate: string | null): boolean {
  if (!endDate) return false
  const end = new Date(endDate)
  const now = new Date()
  return end.getTime() < now.getTime()
}

export function formatDateTime(isoString: string | null): string {
  if (!isoString) return ''
  const d = new Date(isoString)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ============ 循环相关 ============

export const recurrenceOptions = [
  { label: '不循环', value: 'none' },
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' },
  { label: '每年', value: 'yearly' },
  { label: '工作日', value: 'workday' },
  { label: '周末', value: 'weekend' },
  { label: '节假日', value: 'holiday' },
  { label: '自定义', value: 'custom' },
]

export function getRecurrenceText(type: string, interval?: number): string {
  if (type === 'custom') return `每${interval}天`
  return recurrenceOptions.find(o => o.value === type)?.label || type
}

// ============ 状态相关 ============

import { RefreshRight, Clock } from '@element-plus/icons-vue'

export const nextStatusLabel: Record<string, string> = {
  todo: '设为完成',
  done: '重设为待办',
}

export const nextStatusIcon: Record<string, typeof RefreshRight> = {
  todo: RefreshRight,
  done: Clock,
}

// ============ 四象限相关 ============

export function getQuadrant(importance: number, urgency: number): number {
  if (importance >= 50 && urgency >= 50) return 1
  if (importance >= 50) return 2
  if (urgency >= 50) return 3
  return 4
}

export function useSortedByQuadrant(todos: Todo[]) {
  return computed(() => {
    return [...todos].sort((a, b) => {
      // 先按状态排序：待办在前，已完成在后
      if (a.status !== b.status) {
        return a.status === 'todo' ? -1 : 1
      }
      // 同状态下，置顶优先
      if (a.is_pinned !== b.is_pinned) {
        return a.is_pinned ? -1 : 1
      }
      // 按象限排序
      const qa = getQuadrant(a.importance, a.urgency)
      const qb = getQuadrant(b.importance, b.urgency)
      return qa - qb
    })
  })
}

// ============ 进度样式相关 ============

export function useProgressStyle() {
  const themeStore = useThemeStore()

  function getProgressStyle(t: Todo) {
    if (t.recurrence_type === 'none' || t.times_per_interval <= 1) {
      return {}
    }
    const total = Math.max(1, t.times_per_interval)
    const done = Math.min(t.interval_progress || 0, total)
    const pct = Math.floor((done / total) * 100)
    const baseColor = themeStore.isDark ? 'var(--bg-card)' : '#ffffff'
    const progressColor = themeStore.isDark ? 'rgba(103, 194, 58, 0.25)' : 'rgba(103, 194, 58, 0.15)'
    return {
      background: `linear-gradient(to right, ${progressColor} ${pct}%, ${baseColor} ${pct}%)`,
    }
  }

  return { getProgressStyle }
}
