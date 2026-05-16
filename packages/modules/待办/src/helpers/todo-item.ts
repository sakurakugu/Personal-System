import { Clock, RefreshRight } from '@element-plus/icons-vue'
import {
  格式化精确待办日期时间,
  格式化待办日期时间,
  获取待办循环文本,
  获取待办回收站过期时间,
  获取待办回收站剩余删除文本,
  获取待办回收站剩余删除天数,
  是否待办临近截止,
  是否待办逾期,
  解析待办标签,
  是否保留待办强调色 as 共享是否保留待办强调色,
  按状态和置顶创建排序待办 as 共享按状态和置顶创建排序待办,
  TODO_TRASH_RETENTION_DAYS,
  todoNextStatusLabel,
  todoRecurrenceOptions,
  todoStatusLabel,
  todoStatusOrder,
} from '../display'
import { computed } from 'vue'
import type { Todo } from '../store'

export const 回收站保留天数 = TODO_TRASH_RETENTION_DAYS

// ============ 标签相关 ============

export function 解析标签(tags: string[] | null): string[] {
  return 解析待办标签(tags)
}

// ============ 优先级相关 ============

export function 获取优先级标签类型(value: number): 'success' | 'info' | 'warning' | 'danger' {
  if (value >= 86) return 'danger'
  if (value >= 67) return 'warning'
  if (value >= 33) return 'success'
  return 'info'
}

export function 获取优先级标签(value: number): string {
  if (value >= 86) return '非常重要'
  if (value >= 67) return '重要'
  if (value >= 33) return '一般'
  return '不重要'
}

export function 获取优先级强调色(value: number): string {
  if (value >= 86) return 'var(--el-color-danger)'
  if (value >= 67) return 'var(--el-color-warning)'
  if (value >= 33) return 'var(--el-color-success)'
  return 'var(--el-color-info)'
}

// ============ 日期相关 ============

export function 是否临近截止(endDate: string | null): boolean {
  return 是否待办临近截止(endDate)
}

export function 是否逾期(endDate: string | null): boolean {
  return 是否待办逾期(endDate)
}

export function 格式化日期时间(value: string | Date | null): string {
  return 格式化待办日期时间(value)
}

export function 格式化精确日期时间(value: string | Date | null): string {
  return 格式化精确待办日期时间(value)
}

export function 获取回收站过期时间(deletedAt: string | Date | null): Date | null {
  return 获取待办回收站过期时间(deletedAt)
}

export function 获取回收站剩余删除天数(deletedAt: string | Date | null): number | null {
  return 获取待办回收站剩余删除天数(deletedAt)
}

export function 获取回收站剩余删除文本(deletedAt: string | Date | null): string {
  return 获取待办回收站剩余删除文本(deletedAt)
}

// ============ 循环相关 ============

export const recurrenceOptions = [
  ...todoRecurrenceOptions,
]

export function 获取循环文本(type: string, interval?: number): string {
  return 获取待办循环文本(type, interval)
}

export function 是否保留待办强调色(todo: Todo): boolean {
  return 共享是否保留待办强调色(todo)
}

// ============ 状态相关 ============

export const nextStatusLabel: Record<string, string> = {
  ...todoNextStatusLabel,
}

export const statusLabel: Record<string, string> = {
  ...todoStatusLabel,
}

export const statusOrder: Record<string, string> = {
  ...todoStatusOrder,
}

export const nextStatusIcon: Record<string, typeof RefreshRight> = {
  todo: RefreshRight,
  done: Clock,
}

// ============ 四象限相关 ============

export function 获取象限(importance: number, urgency: number): number {
  if (importance >= 50 && urgency >= 50) return 1
  if (importance >= 50) return 2
  if (urgency >= 50) return 3
  return 4
}

export function 按状态和置顶创建排序待办(todos: Todo[]): Todo[] {
  return 共享按状态和置顶创建排序待办(todos)
}

export function 使用按象限排序(todos: Todo[]) {
  return computed(() => {
    return 按状态和置顶创建排序待办(todos).sort((a, b) => {
      // 按象限排序
      const qa = 获取象限(a.importance, a.urgency)
      const qb = 获取象限(b.importance, b.urgency)
      return qa - qb
    })
  })
}

// ============ 进度样式相关 ============

export function 使用进度样式() {
  function 获取进度样式(t: Todo) {
    if (t.recurrence_type === 'none' || t.times_per_interval <= 1) {
      return {}
    }
    const total = Math.max(1, t.times_per_interval)
    const done = Math.min(t.interval_progress || 0, total)
    if (done <= 0) {
      return {}
    }
    const pct = Math.floor((done / total) * 100)
    const isDark = document.documentElement.classList.contains('dark')
    const progressColor = isDark ? 'rgba(103, 194, 58, 0.25)' : 'rgba(103, 194, 58, 0.15)'
    return {
      backgroundImage: `linear-gradient(to right, ${progressColor} ${pct}%, transparent ${pct}%)`,
      backgroundRepeat: 'no-repeat',
    }
  }

  return { getProgressStyle: 获取进度样式 }
}
