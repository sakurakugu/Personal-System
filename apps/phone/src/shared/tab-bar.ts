import { House, Memo, User } from '@element-plus/icons-vue'
import type { Component } from 'vue'

export type AppTabId = 'home' | 'todos' | 'profile'

export interface AppTabDefinition {
  id: AppTabId
  to: string
  label: string
  icon: Component
  required?: boolean
}

export const MIN_VISIBLE_TAB_COUNT = 3

export const APP_TAB_DEFINITIONS: AppTabDefinition[] = [
  { id: 'home', to: '/', label: '首页', icon: House },
  { id: 'todos', to: '/todos', label: '待办', icon: Memo },
  { id: 'profile', to: '/me', label: '我的', icon: User, required: true },
]

export const DEFAULT_APP_TAB_ORDER = APP_TAB_DEFINITIONS.map((item) => item.id)
export const DEFAULT_VISIBLE_APP_TAB_IDS = DEFAULT_APP_TAB_ORDER.slice()
export const REQUIRED_APP_TAB_IDS = APP_TAB_DEFINITIONS.filter((item) => item.required).map((item) => item.id)
export const APP_TAB_DEFINITION_MAP = new Map(APP_TAB_DEFINITIONS.map((item) => [item.id, item]))

export function isAppTabId(value: unknown): value is AppTabId {
  return typeof value === 'string' && APP_TAB_DEFINITION_MAP.has(value as AppTabId)
}
