import type { Component } from 'vue'
import { defineComponent, h } from 'vue'

type 支持返回能力属性 = {
  showBack?: boolean
  backTo?: string
}

export function 创建手机返回页面(
  页面组件: Component<支持返回能力属性>,
  backTo = '/',
) {
  return defineComponent({
    name: '手机返回页面',
    setup() {
      return () => h(页面组件, {
        showBack: true,
        backTo,
      })
    },
  })
}
