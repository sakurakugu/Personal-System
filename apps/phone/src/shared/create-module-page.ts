import type { Component } from 'vue'
import { defineComponent, h } from 'vue'
import { 使用手机页返回能力 } from './page-back'
import type { AppTabId } from './tab-bar'

type 支持返回能力属性 = {
  showBack?: boolean
  backTo?: string
}

export function 创建手机模块页面(
  页面组件: Component<支持返回能力属性>,
  tabId: AppTabId,
  backTo = '/me',
) {
  return defineComponent({
    name: `手机模块页面${tabId}`,
    setup() {
      const { showBack, backTo: resolvedBackTo } = 使用手机页返回能力(tabId, backTo)

      return () => h(页面组件, {
        showBack: showBack.value,
        backTo: resolvedBackTo,
      })
    },
  })
}
