import { ChatDotRound, Collection, Connection, CreditCard, Document, Folder, Grid, House, List, Monitor, Picture, Setting, Tickets, User } from '@element-plus/icons-vue'
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
  { to: '/home', label: '首页', icon: House },
  { to: '/moments', label: '动态', icon: ChatDotRound },
  { to: '/memos', label: '备忘录', icon: Tickets },
  { to: '/todos', label: '待办事项', icon: List },
  { to: '/articles', label: '文章管理', icon: Document },
  { to: '/collections', label: '资料库', icon: Collection },
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
    topNav: { to: '/home', label: '首页', icon: House, section: 'workspace' },
    sidebarTitle: '工作区',
    sidebarItems: workspaceSidebarItems,
    matchTargets: ['/home', '/memos', '/todos', '/collections', '/articles', '/files', '/bills', '/moments', '/device-sessions', '/profile', '/settings', '/settings/api-environment'],
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

export function 桌面导航项是否激活(path: string, target: string) {
  if (target === '/home') {
    return path === target || path.startsWith('/home/')
  }

  return path === target || path.startsWith(`${target}/`)
}

export function 桌面导航项是否匹配(path: string, item: DesktopNavItem) {
  if (item.exact) {
    return path === item.to
  }

  return 桌面导航项是否激活(path, item.to)
}

export function 解析桌面顶栏区域(path: string): DesktopNavSection {
  const matchedSection = desktopNavSections.find((section) => (
    section.matchTargets.some((target) => 桌面导航项是否激活(path, target))
  ))
  return matchedSection?.section ?? 'workspace'
}

export function 获取桌面区域配置(path: string) {
  const currentSection = 解析桌面顶栏区域(path)
  return desktopNavSections.find((section) => section.section === currentSection) ?? desktopNavSections[0]
}

export function 桌面顶栏导航项是否激活(path: string, item: DesktopTopNavItem) {
  return 解析桌面顶栏区域(path) === item.section
}

export function 获取桌面侧栏导航项(path: string): DesktopNavItem[] {
  return 获取桌面区域配置(path).sidebarItems
}

export function 获取桌面侧栏标题(path: string) {
  return 获取桌面区域配置(path).sidebarTitle
}

export function 获取桌面路由标题(path: string) {
  if (path === '/home' || path.startsWith('/home/blog/')) {
    return '首页'
  }
  if (path.startsWith('/home/moments/')) {
    return '首页'
  }
  return 查找桌面导航项(path)?.label ?? 获取桌面区域配置(path).topNav.label
}

export function 查找桌面导航项(path: string): DesktopNavItem | undefined {
  const currentSidebarNavItems = 获取桌面侧栏导航项(path)
  return [...currentSidebarNavItems, ...desktopTopNavItems].find((item) => 桌面导航项是否匹配(path, item))
}
