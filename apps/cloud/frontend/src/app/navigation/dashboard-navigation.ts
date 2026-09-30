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
  Tickets,
  User,
  VideoPlay,
} from '@element-plus/icons-vue'
import type { 控制台菜单项 } from '../components/layout/ConsoleLayout'

export type 仪表盘菜单配置项 = 控制台菜单项

export const 仪表盘菜单配置: 仪表盘菜单配置项[] = [
  { label: '博客管理', key: '/dashboard/blog', icon: Document },
  { label: '博客统计', key: '/dashboard/stats/blog', icon: DataAnalysis },
  { label: '作品推荐', key: '/dashboard/media', icon: VideoPlay },
  { label: '友链管理', key: '/dashboard/friend-links', icon: Link },
  { label: '评论管理', key: '/dashboard/twikoo', icon: ChatDotRound },
  { label: '公告管理', key: '/dashboard/announcements', icon: Bell },
  { label: '系统设置', key: '/dashboard/settings', icon: Setting },
  { label: '数据统计', key: '/dashboard/stats/other', icon: DataAnalysis, dividerBefore: true },
  { label: '动态管理', key: '/dashboard/moments', icon: ChatDotRound },
  { label: '备忘录', key: '/dashboard/memos', icon: Tickets },
  { label: '待办事项', key: '/dashboard/todos', icon: Checked },
  { label: '文章管理', key: '/dashboard/articles', icon: Document },
  { label: '资料库', key: '/dashboard/materials', icon: Collection },
  { label: '文件管理', key: '/dashboard/files', icon: Folder },
  { label: '账单管理', key: '/dashboard/bills', icon: CreditCard },
  { label: '登录设备', key: '/dashboard/device-sessions', icon: Monitor },
  { label: '个人资料', key: '/dashboard/profile', icon: User },
  { label: 'AI 管理', key: '/dashboard/ai', icon: ChatDotRound },
  { label: '系统状态', key: '/dashboard/system', icon: Monitor },
]

export function 过滤仪表盘菜单项(
  items: 仪表盘菜单配置项[] = 仪表盘菜单配置,
): 控制台菜单项[] {
  return items
}
