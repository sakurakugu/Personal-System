import { ChatDotRound, CreditCard, Grid, House, List, Monitor, User } from '@element-plus/icons-vue'
import { 工具侧栏菜单项 } from '@personal-system/modules/tools'
import type { Component } from 'vue'

export type DesktopNavSection = 'workspace' | 'tools'

export interface DesktopNavItem {
  to: string
  label: string
  icon: Component
  disabled?: boolean
}

export interface DesktopTopNavItem extends DesktopNavItem {
  section: DesktopNavSection
}

export interface DesktopNavSectionConfig {
  section: DesktopNavSection
  topNav: DesktopTopNavItem
  sidebarTitle: string
  sidebarItems: DesktopNavItem[]
  matchTargets: string[]
}

const workspaceSidebarItems: DesktopNavItem[] = [
  { to: '/', label: '首页', icon: House },
  { to: '/todos', label: '待办事项', icon: List },
  { to: '/bills', label: '账单管理', icon: CreditCard },
  { to: '/moments', label: '动态', icon: ChatDotRound },
  { to: '/device-sessions', label: '登录设备', icon: Monitor },
  { to: '/profile', label: '账户信息', icon: User },
]

const toolsSidebarItems: DesktopNavItem[] = 工具侧栏菜单项.map((item) => ({
  to: item.key,
  label: item.label,
  icon: item.icon,
  disabled: item.disabled,
}))

export const desktopNavSections: DesktopNavSectionConfig[] = [
  {
    section: 'workspace',
    topNav: { to: '/', label: '首页', icon: House, section: 'workspace' },
    sidebarTitle: '工作区',
    sidebarItems: workspaceSidebarItems,
    matchTargets: ['/', '/todos', '/bills', '/moments', '/device-sessions', '/profile'],
  },
  {
    section: 'tools',
    topNav: { to: '/tools', label: '工具', icon: Grid, section: 'tools' },
    sidebarTitle: '工具箱',
    sidebarItems: toolsSidebarItems,
    matchTargets: ['/tools'],
  },
]

export const desktopTopNavItems = desktopNavSections.map((section) => section.topNav)
export const desktopWorkspaceSidebarNavItems = workspaceSidebarItems
export const desktopToolsSidebarNavItems = toolsSidebarItems
export const desktopNavItems = [
  ...desktopTopNavItems,
  ...desktopWorkspaceSidebarNavItems,
  ...desktopToolsSidebarNavItems,
]

export function isDesktopNavItemActive(path: string, target: string) {
  if (target === '/') {
    return path === target
  }

  return path === target || path.startsWith(`${target}/`)
}

export function resolveDesktopTopNavSection(path: string): DesktopNavSection {
  const matchedSection = desktopNavSections.find((section) => (
    section.matchTargets.some((target) => isDesktopNavItemActive(path, target))
  ))
  return matchedSection?.section ?? 'workspace'
}

export function getDesktopSectionConfig(path: string) {
  const currentSection = resolveDesktopTopNavSection(path)
  return desktopNavSections.find((section) => section.section === currentSection) ?? desktopNavSections[0]
}

export function isDesktopTopNavItemActive(path: string, item: DesktopTopNavItem) {
  return resolveDesktopTopNavSection(path) === item.section
}

export function getDesktopSidebarNavItems(path: string): DesktopNavItem[] {
  return getDesktopSectionConfig(path).sidebarItems
}

export function getDesktopSidebarTitle(path: string) {
  return getDesktopSectionConfig(path).sidebarTitle
}

export function getDesktopRouteTitle(path: string) {
  return findDesktopNavItem(path)?.label ?? getDesktopSectionConfig(path).topNav.label
}

export function findDesktopNavItem(path: string): DesktopNavItem | undefined {
  const currentSidebarNavItems = getDesktopSidebarNavItems(path)
  return [...currentSidebarNavItems, ...desktopTopNavItems].find((item) => isDesktopNavItemActive(path, item.to))
}
