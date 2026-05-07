import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { findDesktopNavItem, getDesktopRouteTitle } from '../../app/navigation'

export interface DesktopTabItem {
  id: string
  path: string
  title: string
}

function createTabId() {
  return `desktop-tab-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function createTab(path: string): DesktopTabItem {
  return {
    id: createTabId(),
    path,
    title: getDesktopRouteTitle(path),
  }
}

export const useDesktopTabsStore = defineStore('desktop-tabs', () => {
  const tabs = ref<DesktopTabItem[]>([])
  const activeTabId = ref('')
  const initialized = ref(false)

  const activeTab = computed(() => {
    return tabs.value.find((tab) => tab.id === activeTabId.value) ?? null
  })

  function ensureDefaultTab(path: string) {
    if (tabs.value.length > 0) {
      return
    }

    const tab = createTab(path)
    tabs.value = [tab]
    activeTabId.value = tab.id
  }

  function init(path: string) {
    if (initialized.value) {
      syncActiveRoute(path)
      return
    }

    initialized.value = true
    ensureDefaultTab(path)
  }

  function syncActiveRoute(path: string) {
    ensureDefaultTab(path)

    const currentTab = activeTab.value
    if (!currentTab) {
      return
    }

    if (currentTab.path === path) {
      currentTab.title = getDesktopRouteTitle(path)
      return
    }

    const matchedTab = tabs.value.find((tab) => tab.path === path)
    if (matchedTab) {
      matchedTab.title = getDesktopRouteTitle(path)
      activeTabId.value = matchedTab.id
      return
    }

    currentTab.path = path
    currentTab.title = getDesktopRouteTitle(path)
  }

  function addTab(path = '/') {
    const nextTab = createTab(path)
    tabs.value.push(nextTab)
    activeTabId.value = nextTab.id
    return nextTab
  }

  function activateTab(id: string) {
    if (!tabs.value.some((tab) => tab.id === id)) {
      return null
    }

    activeTabId.value = id
    return tabs.value.find((tab) => tab.id === id) ?? null
  }

  function openRoute(path: string) {
    const existingTab = tabs.value.find((tab) => tab.path === path)
    if (existingTab) {
      activeTabId.value = existingTab.id
      existingTab.title = getDesktopRouteTitle(path)
      return existingTab
    }

    return addTab(path)
  }

  function closeTab(id: string) {
    const index = tabs.value.findIndex((tab) => tab.id === id)
    if (index < 0) {
      return null
    }

    const closingActive = activeTabId.value === id
    tabs.value.splice(index, 1)

    if (tabs.value.length === 0) {
      const fallbackTab = createTab('/')
      tabs.value = [fallbackTab]
      activeTabId.value = fallbackTab.id
      return fallbackTab
    }

    if (!closingActive) {
      return activeTab.value
    }

    const nextActiveTab = tabs.value[Math.max(index - 1, 0)] ?? tabs.value[0] ?? null
    activeTabId.value = nextActiveTab?.id ?? ''
    return nextActiveTab
  }

  function reset(path = '/') {
    const nextTab = createTab(path)
    tabs.value = [nextTab]
    activeTabId.value = nextTab.id
    initialized.value = false
  }

  function getTabIcon(path: string) {
    return findDesktopNavItem(path)?.icon ?? null
  }

  return {
    tabs,
    activeTabId,
    activeTab,
    init,
    syncActiveRoute,
    addTab,
    activateTab,
    openRoute,
    closeTab,
    reset,
    getTabIcon,
  }
})
