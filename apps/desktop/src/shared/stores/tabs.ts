import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { 查找桌面导航项, 获取桌面区域配置, 获取桌面路由标题 } from '../../app/navigation'

export interface DesktopTabItem {
  id: string
  path: string
  title: string
}

function 创建标签页ID() {
  return `desktop-tab-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function 创建标签页(path: string): DesktopTabItem {
  return {
    id: 创建标签页ID(),
    path,
    title: 获取桌面路由标题(path),
  }
}

function 获取标签清空后的回退路径(path: string) {
  return 获取桌面区域配置(path).topNav.to
}

export const 使用桌面标签存储 = defineStore('desktop-tabs', () => {
  const tabs = ref<DesktopTabItem[]>([])
  const activeTabId = ref('')
  const initialized = ref(false)

  const activeTab = computed(() => {
    return tabs.value.find((tab) => tab.id === activeTabId.value) ?? null
  })

  function 确保默认标签页(path: string) {
    if (tabs.value.length > 0) {
      return
    }

    const tab = 创建标签页(path)
    tabs.value = [tab]
    activeTabId.value = tab.id
  }

  function 初始化(path: string) {
    if (initialized.value) {
      同步活跃路由(path)
      return
    }

    initialized.value = true
    确保默认标签页(path)
  }

  function 同步活跃路由(path: string) {
    确保默认标签页(path)

    const currentTab = activeTab.value
    if (!currentTab) {
      return
    }

    if (currentTab.path === path) {
      currentTab.title = 获取桌面路由标题(path)
      return
    }

    const matchedTab = tabs.value.find((tab) => tab.path === path)
    if (matchedTab) {
      matchedTab.title = 获取桌面路由标题(path)
      activeTabId.value = matchedTab.id
      return
    }

    currentTab.path = path
    currentTab.title = 获取桌面路由标题(path)
  }

  function 添加标签页(path = '/home') {
    const nextTab = 创建标签页(path)
    tabs.value.push(nextTab)
    activeTabId.value = nextTab.id
    return nextTab
  }

  function 确保回退标签页(path = '/home') {
    if (tabs.value.length > 0) {
      return null
    }

    const fallbackPath = 获取标签清空后的回退路径(path)
    console.info('桌面标签已全部关闭，正在创建回退标签页', {
      原始路径: path,
      回退路径: fallbackPath,
    })
    const fallbackTab = 创建标签页(fallbackPath)
    tabs.value = [fallbackTab]
    activeTabId.value = fallbackTab.id
    return fallbackTab
  }

  function 激活标签页(id: string) {
    if (!tabs.value.some((tab) => tab.id === id)) {
      return null
    }

    activeTabId.value = id
    return tabs.value.find((tab) => tab.id === id) ?? null
  }

  function 打开路由(path: string) {
    const existingTab = tabs.value.find((tab) => tab.path === path)
    if (existingTab) {
      activeTabId.value = existingTab.id
      existingTab.title = 获取桌面路由标题(path)
      return existingTab
    }

    return 添加标签页(path)
  }

  function 关闭标签页(id: string) {
    const index = tabs.value.findIndex((tab) => tab.id === id)
    if (index < 0) {
      return null
    }

    const closingTab = tabs.value[index]
    const closingActive = activeTabId.value === id
    tabs.value.splice(index, 1)

    const fallbackTab = 确保回退标签页(closingTab.path)
    if (fallbackTab) {
      return fallbackTab
    }

    if (!closingActive) {
      return activeTab.value
    }

    const nextActiveTab = tabs.value[Math.max(index - 1, 0)] ?? tabs.value[0] ?? null
    activeTabId.value = nextActiveTab?.id ?? ''
    return nextActiveTab
  }

  function 关闭其他标签页(id: string) {
    const targetTab = tabs.value.find((tab) => tab.id === id)
    if (!targetTab) {
      return null
    }

    tabs.value = [targetTab]
    activeTabId.value = targetTab.id
    return targetTab
  }

  function 关闭右侧标签页(id: string) {
    const index = tabs.value.findIndex((tab) => tab.id === id)
    if (index < 0) {
      return null
    }

    const remainingTabs = tabs.value.slice(0, index + 1)
    const activeTabStillExists = remainingTabs.some((tab) => tab.id === activeTabId.value)
    tabs.value = remainingTabs

    const fallbackTab = 确保回退标签页()
    if (fallbackTab) {
      return fallbackTab
    }

    if (activeTabStillExists) {
      return activeTab.value
    }

    const nextActiveTab = tabs.value[index] ?? tabs.value[tabs.value.length - 1] ?? null
    activeTabId.value = nextActiveTab?.id ?? ''
    return nextActiveTab
  }

  function 重置(path = '/home') {
    const nextTab = 创建标签页(path)
    tabs.value = [nextTab]
    activeTabId.value = nextTab.id
    initialized.value = false
  }

  function 获取标签页图标(path: string) {
    return 查找桌面导航项(path)?.icon ?? null
  }

  return {
    tabs,
    activeTabId,
    activeTab,
    init: 初始化,
    syncActiveRoute: 同步活跃路由,
    addTab: 添加标签页,
    activateTab: 激活标签页,
    openRoute: 打开路由,
    closeTab: 关闭标签页,
    closeOtherTabs: 关闭其他标签页,
    closeTabsToRight: 关闭右侧标签页,
    reset: 重置,
    getTabIcon: 获取标签页图标,
  }
})
