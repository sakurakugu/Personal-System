import {
  Bell,
  ChatDotRound,
  Checked,
  Collection,
  CreditCard,
  DataAnalysis,
  Document,
  Folder,
  Link,
  Monitor,
  Setting,
  User,
} from '@element-plus/icons-vue'
import type { 控制台菜单项 } from '../components/layout/ConsoleLayout'

type 仪表盘菜单访问级别 = 'all' | 'admin' | 'super-admin'

export type 仪表盘菜单配置项 = 控制台菜单项 & {
  access?: 仪表盘菜单访问级别
}

export type 仪表盘菜单过滤上下文 = {
  isAdmin: boolean
  isSuperAdmin: boolean
}

export const 仪表盘菜单配置: 仪表盘菜单配置项[] = [
  { label: '数据统计', key: '/dashboard', icon: DataAnalysis },
  { label: '动态管理', key: '/dashboard/moments', icon: ChatDotRound },
  { label: '待办事项', key: '/dashboard/todos', icon: Checked },
  { label: '文章管理', key: '/dashboard/articles', icon: Document },
  { label: '收藏收纳库', key: '/dashboard/collections', icon: Collection },
  { label: '文件管理', key: '/dashboard/files', icon: Folder },
  { label: '账单管理', key: '/dashboard/bills', icon: CreditCard },
  { label: '登录设备', key: '/dashboard/device-sessions', icon: Monitor },
  { label: '个人资料', key: '/dashboard/profile', icon: User },
  { label: '用户设置', key: '/dashboard/user-settings', icon: Setting },
  { label: '用户管理', key: '/dashboard/users', icon: User, dividerBefore: true, access: 'admin' },
  { label: '友链管理', key: '/dashboard/friend-links', icon: Link, dividerBefore: true, access: 'super-admin' },
  { label: '评论管理', key: '/dashboard/twikoo', icon: ChatDotRound, access: 'super-admin' },
  { label: '系统状态', key: '/dashboard/system', icon: Monitor, access: 'super-admin' },
  { label: '公告管理', key: '/dashboard/announcements', icon: Bell, access: 'super-admin' },
  { label: '系统设置', key: '/dashboard/settings', icon: Setting, access: 'super-admin' },
]

export function 过滤仪表盘菜单项(
  context: 仪表盘菜单过滤上下文,
  items: 仪表盘菜单配置项[] = 仪表盘菜单配置,
): 控制台菜单项[] {
  return items.filter((item) => {
    if (item.access === 'super-admin') {
      return context.isSuperAdmin
    }
    if (item.access === 'admin') {
      return context.isAdmin
    }
    return true
  })
}
