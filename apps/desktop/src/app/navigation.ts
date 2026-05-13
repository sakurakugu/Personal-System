import { ChatDotRound, Collection, Connection, CreditCard, Document, Folder, Grid, House, List, Monitor, Picture, Setting, User } from '@element-plus/icons-vue'
import type { Component } from 'vue'

export type DesktopNavSection = 'workspace' | 'tools'

export interface DesktopNavItem {
  to: string
  label: string
  icon: Component
  disabled?: boolean
  exact?: boolean
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
  { to: '/moments', label: '动态', icon: ChatDotRound },
  { to: '/todos', label: '待办事项', icon: List },
  { to: '/articles', label: '文章管理', icon: Document },
  { to: '/collections', label: '收藏收纳', icon: Collection },
  { to: '/files', label: '文件管理', icon: Folder },
  { to: '/bills', label: '账单管理', icon: CreditCard },
  { to: '/device-sessions', label: '登录设备', icon: Monitor },
  { to: '/profile', label: '账户信息', icon: User },
  { to: '/settings', label: '设置', icon: Setting },
]

const toolsSidebarItems: DesktopNavItem[] = [
  { to: '/tools', label: '工具首页', icon: Grid, exact: true },
  { to: '/tools/image', label: '图片工具', icon: Picture },
  { to: '/tools/windows', label: 'Windows 工具', icon: Monitor },
  { to: '/tools/image-classifier', label: '图片分类', icon: Grid },
  { to: '/tools/minecraft-server', label: 'MC 服务器查询', icon: Connection },
]

export const desktopNavSections: DesktopNavSectionConfig[] = [
  {
    section: 'workspace',
    topNav: { to: '/', label: '首页', icon: House, section: 'workspace' },
    sidebarTitle: '工作区',
    sidebarItems: workspaceSidebarItems,
    matchTargets: ['/', '/todos', '/collections', '/articles', '/files', '/bills', '/moments', '/device-sessions', '/profile', '/settings', '/settings/api-environment'],
  },
  {
    section: 'tools',
    topNav: { to: '/tools', label: '工具', icon: Grid, section: 'tools' },
    sidebarTitle: '工具箱',
    sidebarItems: toolsSidebarItems,
    matchTargets: ['/tools', '/tools/image', '/tools/windows', '/tools/image-classifier', '/tools/minecraft-server'],
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

export function isDesktopNavItemMatched(path: string, item: DesktopNavItem) {
  if (item.exact) {
    return path === item.to
  }

  return isDesktopNavItemActive(path, item.to)
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
  if (path === '/widget') {
    return '桌面小工具'
  }
  return findDesktopNavItem(path)?.label ?? getDesktopSectionConfig(path).topNav.label
}

export function findDesktopNavItem(path: string): DesktopNavItem | undefined {
  const currentSidebarNavItems = getDesktopSidebarNavItems(path)
  return [...currentSidebarNavItems, ...desktopTopNavItems].find((item) => isDesktopNavItemMatched(path, item))
}
