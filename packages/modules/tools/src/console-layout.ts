import type { Component } from 'vue'

export type 工具侧栏模式 = 'expanded' | 'compact' | 'hidden'

export type 工具菜单项 = {
  label: string
  key: string
  icon: Component
  disabled?: boolean
  dividerBefore?: boolean
}
