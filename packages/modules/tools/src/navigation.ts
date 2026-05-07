import { MagicStick, PictureFilled } from '@element-plus/icons-vue'
import type { 工具菜单项 } from './console-layout'

export const 工具侧栏菜单项: 工具菜单项[] = [
  { label: '图片编辑', key: '/tools', icon: PictureFilled },
  { label: '更多工具', key: '/tools/more', icon: MagicStick, disabled: true },
]
