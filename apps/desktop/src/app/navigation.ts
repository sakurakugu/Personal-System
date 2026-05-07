import { House, Monitor, User } from '@element-plus/icons-vue'
import type { Component } from 'vue'

export interface DesktopNavItem {
  to: string
  label: string
  icon: Component
}

export const desktopNavItems: DesktopNavItem[] = [
  { to: '/', label: '概览', icon: House },
  { to: '/device-sessions', label: '登录设备', icon: Monitor },
  { to: '/profile', label: '账户信息', icon: User },
]

export function findDesktopNavItem(path: string): DesktopNavItem | undefined {
  return desktopNavItems.find((item) => item.to === path)
}
