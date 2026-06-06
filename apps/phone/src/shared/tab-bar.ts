import { ChatDotRound, Collection, CreditCard, Document, House, Memo, Tickets, User } from '@element-plus/icons-vue'
import type { Component } from 'vue'

export type AppTabId =
  | 'home'
  | 'memos'
  | 'todos'
  | 'moments'
  | 'articles'
  | 'materials'
  | 'bills'
  | 'profile'

export interface AppTabDefinition {
  id: AppTabId
  to: string
  label: string
  icon: Component
  required?: boolean
}

export const MIN_VISIBLE_TAB_COUNT = 3
export const MAX_VISIBLE_TAB_COUNT = 5

export const APP_TAB_DEFINITIONS: AppTabDefinition[] = [
  { id: 'home', to: '/', label: '首页', icon: House },
  { id: 'memos', to: '/memos', label: '备忘', icon: Tickets },
  { id: 'todos', to: '/todos', label: '待办', icon: Memo },
  { id: 'moments', to: '/moments', label: '动态', icon: ChatDotRound },
  { id: 'articles', to: '/articles', label: '文章', icon: Document },
  { id: 'materials', to: '/materials', label: '资料', icon: Collection },
  { id: 'bills', to: '/bills', label: '账单', icon: CreditCard },
  { id: 'profile', to: '/me', label: '我的', icon: User, required: true },
]

export const DEFAULT_APP_TAB_ORDER = APP_TAB_DEFINITIONS.map((item) => item.id)
export const DEFAULT_VISIBLE_APP_TAB_IDS: AppTabId[] = ['home', 'memos', 'todos', 'profile']
export const REQUIRED_APP_TAB_IDS = APP_TAB_DEFINITIONS.filter((item) => item.required).map((item) => item.id)
export const APP_TAB_DEFINITION_MAP = new Map(APP_TAB_DEFINITIONS.map((item) => [item.id, item]))

export function 是否为应用标签页ID(value: unknown): value is AppTabId {
  return typeof value === 'string' && APP_TAB_DEFINITION_MAP.has(value as AppTabId)
}
