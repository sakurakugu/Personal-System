import { computed } from 'vue'
import { 使用标签栏存储 } from './stores/tab-bar'
import type { AppTabId } from './tab-bar'

export function 使用手机页返回能力(tabId: AppTabId, backTo = '/') {
  const tabBar = 使用标签栏存储()

  const showBack = computed(() => {
    return !tabBar.visibleTabIds.includes(tabId)
  })

  return {
    showBack,
    backTo,
  }
}
