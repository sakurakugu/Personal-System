import { MagicStick, PictureFilled, Upload } from '@element-plus/icons-vue'
import type { 工具菜单项 } from './ConsoleLayout'

export type 工具入口可见性上下文 = {
  isAuthenticated: boolean
}

export type 工具菜单配置项 = 工具菜单项 & {
  requiresAuth?: boolean
}

export const 工具侧栏菜单配置: 工具菜单配置项[] = [
  { label: '工具首页', key: '/tools', icon: MagicStick, exact: true },
  { label: '图片工具', key: '/tools/image', icon: PictureFilled },
  { label: '文件中转站', key: '/tools/transfer', icon: Upload, requiresAuth: true },
]

export const 工具侧栏菜单项: 工具菜单项[] = 工具侧栏菜单配置

export function 过滤工具侧栏菜单项(
  context: 工具入口可见性上下文,
  items: 工具菜单配置项[] = 工具侧栏菜单配置,
): 工具菜单项[] {
  return items.filter((item) => {
    if (item.requiresAuth) {
      return context.isAuthenticated
    }
    return true
  })
}
