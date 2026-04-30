import { Clock, RefreshRight } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useThemeStore } from '../../../shared/stores/theme'
import type { Todo } from '../store'

const 一天毫秒数 = 24 * 60 * 60 * 1000
export const 回收站保留天数 = 90

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

export function getPriorityAccentColor(value: number): string {
  if (value >= 86) return 'var(--el-color-danger)'
  if (value >= 67) return 'var(--el-color-warning)'
  if (value >= 33) return 'var(--el-color-success)'
  return 'var(--el-color-info)'
}

// ============ 日期相关 ============

function 解析日期输入(value: string | Date | null): Date | null {
  if (!value) return null
  const date = value instanceof Date ? new Date(value.getTime()) : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function 补零(value: number): string {
  return String(value).padStart(2, '0')
}

export function isNearDeadline(endDate: string | null): boolean {
  const end = 解析日期输入(endDate)
  if (!end) return false
  const now = new Date()
  const diff = end.getTime() - now.getTime()
  return diff > 0 && diff < 24 * 60 * 60 * 1000
}

export function isOverdue(endDate: string | null): boolean {
  const end = 解析日期输入(endDate)
  if (!end) return false
  const now = new Date()
  return end.getTime() < now.getTime()
}

export function formatDateTime(value: string | Date | null): string {
  const date = 解析日期输入(value)
  if (!date) return ''
  return `${date.getMonth() + 1}/${date.getDate()} ${补零(date.getHours())}:${补零(date.getMinutes())}`
}

export function formatPreciseDateTime(value: string | Date | null): string {
  const date = 解析日期输入(value)
  if (!date) return ''
  return `${date.getFullYear()}-${补零(date.getMonth() + 1)}-${补零(date.getDate())} ${补零(date.getHours())}:${补零(date.getMinutes())}`
}

export function getTrashExpireAt(deletedAt: string | Date | null): Date | null {
  const deletedDate = 解析日期输入(deletedAt)
  if (!deletedDate) return null
  return new Date(deletedDate.getTime() + 回收站保留天数 * 一天毫秒数)
}

export function getTrashRemainingDeleteDays(deletedAt: string | Date | null): number | null {
  const expireAt = getTrashExpireAt(deletedAt)
  if (!expireAt) return null

  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.max(0, Math.floor((expireAt.getTime() - todayStart.getTime()) / 一天毫秒数))
}

export function getTrashRemainingDeleteText(deletedAt: string | Date | null): string {
  const remainingDays = getTrashRemainingDeleteDays(deletedAt)
  if (remainingDays === null) return '等待自动删除'
  return `还剩${remainingDays}天删除`
}

// ============ 循环相关 ============

export const recurrenceOptions = [
  { label: '不循环', value: 'none' },
  { label: '每天', value: 'daily' },
  { label: '每周', value: 'weekly' },
  { label: '每月', value: 'monthly' },
  { label: '每年', value: 'yearly' },
  { label: '工作日（含调休）', value: 'workday' },
  { label: '周末（周六、周日）', value: 'weekend' },
  { label: '节假日(含周末）', value: 'holiday' },
  { label: '自定义', value: 'custom' },
]

export function getRecurrenceText(type: string, interval?: number): string {
  if (type === 'custom') return `每${interval}天`
  return recurrenceOptions.find(o => o.value === type)?.label || type
}

export function shouldKeepTodoAccentColor(todo: Todo): boolean {
  if (todo.status !== 'done') return false

  const nextResetAt = 解析日期输入(todo.progress_reset_at)
  if (!nextResetAt) return false

  const deadline = 解析日期输入(todo.end_date)
  if (!deadline) return true

  return nextResetAt.getTime() <= deadline.getTime()
}

// ============ 状态相关 ============

export const nextStatusLabel: Record<string, string> = {
  todo: '设为完成',
  done: '重设为待办',
}

export const statusLabel: Record<string, string> = {
  todo: '待办',
  done: '已完成',
}

export const statusOrder: Record<string, string> = {
  todo: 'done',
  done: 'todo',
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

export function sortTodosByStatusAndPinCreated(todos: Todo[]): Todo[] {
  return [...todos].sort((a, b) => {
    // 先按状态排序：待办在前，已完成在后
    if (a.status !== b.status) {
      return a.status === 'todo' ? -1 : 1
    }
    // 同状态下，置顶优先
    if (a.is_pinned !== b.is_pinned) {
      return a.is_pinned ? -1 : 1
    }
    // 最后按创建时间倒序
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
}

export function useSortedByQuadrant(todos: Todo[]) {
  return computed(() => {
    return sortTodosByStatusAndPinCreated(todos).sort((a, b) => {
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
    if (done <= 0) {
      return {}
    }
    const pct = Math.floor((done / total) * 100)
    const progressColor = themeStore.isDark ? 'rgba(103, 194, 58, 0.25)' : 'rgba(103, 194, 58, 0.15)'
    return {
      backgroundImage: `linear-gradient(to right, ${progressColor} ${pct}%, transparent ${pct}%)`,
      backgroundRepeat: 'no-repeat',
    }
  }

  return { getProgressStyle }
}
