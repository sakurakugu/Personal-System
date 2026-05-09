import type { Component } from 'vue'

export type 侧栏模式 = 'expanded' | 'compact' | 'hidden'

export type 侧栏菜单项 = {
  label: string
  key: string
  icon: Component
  disabled?: boolean
  dividerBefore?: boolean
  exact?: boolean
}

export type 侧栏布局配置 = {
  默认展开宽度?: number
  紧凑宽度?: number
  最小展开宽度?: number
  最大展开宽度?: number
  启用拖拽的最小视口宽度?: number
  主内容最小宽度?: number
  自动收紧比例?: number
  自动展开比例?: number
  隐藏触发器最小底部间距?: number
  隐藏触发器默认底部偏移?: number
}
