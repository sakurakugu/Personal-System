import { Grid, House, MagicStick, Monitor, PictureFilled, User } from '@element-plus/icons-vue'
import type { Component } from 'vue'

export interface DesktopNavItem {
  to: string
  label: string
  icon: Component
  disabled?: boolean
}

export interface DesktopTopNavItem extends DesktopNavItem {
  section: 'workspace' | 'tools'
}

export const desktopTopNavItems: DesktopTopNavItem[] = [
  { to: '/', label: '首页', icon: House, section: 'workspace' },
  { to: '/tools', label: '工具', icon: Grid, section: 'tools' },
]

export const desktopWorkspaceSidebarNavItems: DesktopNavItem[] = [
  { to: '/', label: '首页', icon: House },
  { to: '/device-sessions', label: '登录设备', icon: Monitor },
  { to: '/profile', label: '账户信息', icon: User },
]

export const desktopToolsSidebarNavItems: DesktopNavItem[] = [
  { to: '/tools', label: '图片编辑', icon: PictureFilled },
  { to: '/tools/more', label: '更多工具', icon: MagicStick, disabled: true },
]

const desktopRouteNavItems = [
  ...desktopWorkspaceSidebarNavItems,
  ...desktopToolsSidebarNavItems,
  ...desktopTopNavItems,
]

export function isDesktopNavItemActive(path: string, target: string) {
  if (target === '/') {
    return path === target
  }

  return path === target || path.startsWith(`${target}/`)
}

export function resolveDesktopTopNavSection(path: string): DesktopTopNavItem['section'] {
  return isDesktopNavItemActive(path, '/tools') ? 'tools' : 'workspace'
}

export function isDesktopTopNavItemActive(path: string, item: DesktopTopNavItem) {
  return resolveDesktopTopNavSection(path) === item.section
}

export function getDesktopSidebarNavItems(path: string): DesktopNavItem[] {
  return resolveDesktopTopNavSection(path) === 'tools'
    ? desktopToolsSidebarNavItems
    : desktopWorkspaceSidebarNavItems
}

export function findDesktopNavItem(path: string): DesktopNavItem | undefined {
  const currentSidebarNavItems = getDesktopSidebarNavItems(path)
  return [...currentSidebarNavItems, ...desktopRouteNavItems].find((item) => isDesktopNavItemActive(path, item.to))
}
