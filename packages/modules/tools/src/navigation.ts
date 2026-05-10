import { Connection, MagicStick, PictureFilled } from '@element-plus/icons-vue'
import type { 工具菜单项 } from './console-layout'

export const 工具侧栏菜单项: 工具菜单项[] = [
  { label: '工具首页', key: '/tools', icon: MagicStick, exact: true },
  { label: '图片工具', key: '/tools/image', icon: PictureFilled },
  { label: 'MC 服务器查询', key: '/tools/minecraft-server', icon: Connection },
]
