import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  APP_TAB_DEFINITION_MAP,
  DEFAULT_APP_TAB_ORDER,
  DEFAULT_VISIBLE_APP_TAB_IDS,
  isAppTabId,
  MAX_VISIBLE_TAB_COUNT,
  MIN_VISIBLE_TAB_COUNT,
  REQUIRED_APP_TAB_IDS,
  type AppTabId,
} from '../tab-bar'

interface TabBarPreferencesPayload {
  orderedTabIds?: unknown
  visibleTabIds?: unknown
}

const STORAGE_KEY = 'personal-system:phone:tab-bar'

function normalizeOrderedTabIds(ids: readonly AppTabId[]): AppTabId[] {
  const uniqueIds: AppTabId[] = []

  for (const id of ids) {
    if (!APP_TAB_DEFINITION_MAP.has(id) || uniqueIds.includes(id)) {
      continue
    }
    uniqueIds.push(id)
  }

  for (const id of DEFAULT_APP_TAB_ORDER) {
    if (!uniqueIds.includes(id)) {
      uniqueIds.push(id)
    }
  }

  return uniqueIds
}

function normalizeVisibleTabIds(ids: readonly AppTabId[], orderedTabIds: readonly AppTabId[]): AppTabId[] {
  const requestedVisibleSet = new Set<AppTabId>()

  for (const id of ids) {
    if (APP_TAB_DEFINITION_MAP.has(id)) {
      requestedVisibleSet.add(id)
    }
  }

  const visibleSet = new Set<AppTabId>()

  for (const id of REQUIRED_APP_TAB_IDS) {
    visibleSet.add(id)
  }

  for (const id of orderedTabIds) {
    if (visibleSet.size >= MAX_VISIBLE_TAB_COUNT) {
      break
    }
    if (requestedVisibleSet.has(id) || visibleSet.size < MIN_VISIBLE_TAB_COUNT) {
      visibleSet.add(id)
    }
  }

  return orderedTabIds.filter((id) => visibleSet.has(id))
}

function parseTabIds(value: unknown): AppTabId[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter(isAppTabId)
}

export const useTabBarStore = defineStore('phone-tab-bar', () => {
  const orderedTabIds = ref<AppTabId[]>(DEFAULT_APP_TAB_ORDER.slice())
  const visibleTabIds = ref<AppTabId[]>(DEFAULT_VISIBLE_APP_TAB_IDS.slice())
  const initialized = ref(false)

  const orderedTabs = computed(() => {
    return orderedTabIds.value.map((id) => APP_TAB_DEFINITION_MAP.get(id)).filter((item) => item !== undefined)
  })

  const visibleTabs = computed(() => {
    const visibleSet = new Set(visibleTabIds.value)
    return orderedTabs.value.filter((item) => visibleSet.has(item.id))
  })

  const settingsItems = computed(() => {
    const visibleSet = new Set(visibleTabIds.value)

    return orderedTabs.value.map((item, index) => {
      const visible = visibleSet.has(item.id)
      const required = item.required === true
      const canHide = visible && !required && visibleTabIds.value.length > MIN_VISIBLE_TAB_COUNT
      const canShow = !visible && visibleTabIds.value.length < MAX_VISIBLE_TAB_COUNT

      return {
        ...item,
        visible,
        required,
        canHide,
        canShow,
        canMoveLeft: index > 0,
        canMoveRight: index < orderedTabs.value.length - 1,
      }
    })
  })

  function applyPreferences(nextOrderedTabIds: readonly AppTabId[], nextVisibleTabIds: readonly AppTabId[]) {
    const normalizedOrderedTabIds = normalizeOrderedTabIds(nextOrderedTabIds)
    const normalizedVisibleTabIds = normalizeVisibleTabIds(nextVisibleTabIds, normalizedOrderedTabIds)

    orderedTabIds.value = normalizedOrderedTabIds
    visibleTabIds.value = normalizedVisibleTabIds
  }

  function savePreferences() {
    const payload = {
      orderedTabIds: orderedTabIds.value,
      visibleTabIds: visibleTabIds.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  }

  function init() {
    if (initialized.value) {
      return
    }
    initialized.value = true

    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      applyPreferences(DEFAULT_APP_TAB_ORDER, DEFAULT_VISIBLE_APP_TAB_IDS)
      return
    }

    try {
      const parsed = JSON.parse(raw) as TabBarPreferencesPayload
      applyPreferences(
        parseTabIds(parsed.orderedTabIds),
        parseTabIds(parsed.visibleTabIds),
      )
    } catch {
      // 本地配置损坏时直接回退默认值，避免底部导航不可用。
      applyPreferences(DEFAULT_APP_TAB_ORDER, DEFAULT_VISIBLE_APP_TAB_IDS)
    }
  }

  function setTabVisible(id: AppTabId, visible: boolean) {
    const exists = orderedTabIds.value.includes(id)
    if (!exists) {
      return false
    }

    const isVisible = visibleTabIds.value.includes(id)
    if (visible === isVisible) {
      return true
    }

    if (visible) {
      if (visibleTabIds.value.length >= MAX_VISIBLE_TAB_COUNT) {
        return false
      }
      const visibleSet = new Set(visibleTabIds.value)
      visibleSet.add(id)
      applyPreferences(
        orderedTabIds.value,
        orderedTabIds.value.filter((tabId) => visibleSet.has(tabId)),
      )
      savePreferences()
      return true
    }

    if (REQUIRED_APP_TAB_IDS.includes(id) || visibleTabIds.value.length <= MIN_VISIBLE_TAB_COUNT) {
      return false
    }

    applyPreferences(
      orderedTabIds.value,
      visibleTabIds.value.filter((tabId) => tabId !== id),
    )
    savePreferences()
    return true
  }

  function moveTab(id: AppTabId, direction: -1 | 1) {
    const index = orderedTabIds.value.indexOf(id)
    if (index < 0) {
      return false
    }

    const targetIndex = index + direction
    if (targetIndex < 0 || targetIndex >= orderedTabIds.value.length) {
      return false
    }

    const nextOrderedTabIds = orderedTabIds.value.slice()
    const [targetId] = nextOrderedTabIds.splice(index, 1)
    nextOrderedTabIds.splice(targetIndex, 0, targetId)

    applyPreferences(nextOrderedTabIds, visibleTabIds.value)
    savePreferences()
    return true
  }

  return {
    orderedTabIds,
    visibleTabIds,
    visibleTabs,
    settingsItems,
    minimumVisibleTabCount: MIN_VISIBLE_TAB_COUNT,
    maximumVisibleTabCount: MAX_VISIBLE_TAB_COUNT,
    init,
    setTabVisible,
    moveTab,
  }
})
