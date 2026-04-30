import type { Component } from 'vue'

export type 控制台侧栏模式 = 'expanded' | 'compact' | 'hidden'

export type 控制台菜单项 = {
  label: string
  key: string
  icon: Component
  disabled?: boolean
  dividerBefore?: boolean
}
