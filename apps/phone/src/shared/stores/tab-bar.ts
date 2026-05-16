import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  APP_TAB_DEFINITION_MAP,
  DEFAULT_APP_TAB_ORDER,
  DEFAULT_VISIBLE_APP_TAB_IDS,
  是否为应用标签页ID,
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

function 标准化有序标签页ID(ids: readonly AppTabId[]): AppTabId[] {
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

function 标准化可见标签页ID(ids: readonly AppTabId[], orderedTabIds: readonly AppTabId[]): AppTabId[] {
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

function 解析标签页ID列表(value: unknown): AppTabId[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter(是否为应用标签页ID)
}

export const 使用标签栏存储 = defineStore('phone-tab-bar', () => {
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

  function 应用偏好(nextOrderedTabIds: readonly AppTabId[], nextVisibleTabIds: readonly AppTabId[]) {
    const normalizedOrderedTabIds = 标准化有序标签页ID(nextOrderedTabIds)
    const normalizedVisibleTabIds = 标准化可见标签页ID(nextVisibleTabIds, normalizedOrderedTabIds)

    orderedTabIds.value = normalizedOrderedTabIds
    visibleTabIds.value = normalizedVisibleTabIds
  }

  function 保存偏好() {
    const payload = {
      orderedTabIds: orderedTabIds.value,
      visibleTabIds: visibleTabIds.value,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  }

  function 初始化() {
    if (initialized.value) {
      return
    }
    initialized.value = true

    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      应用偏好(DEFAULT_APP_TAB_ORDER, DEFAULT_VISIBLE_APP_TAB_IDS)
      return
    }

    try {
      const parsed = JSON.parse(raw) as TabBarPreferencesPayload
      应用偏好(
        解析标签页ID列表(parsed.orderedTabIds),
        解析标签页ID列表(parsed.visibleTabIds),
      )
    } catch {
      // 本地配置损坏时直接回退默认值，避免底部导航不可用。
      应用偏好(DEFAULT_APP_TAB_ORDER, DEFAULT_VISIBLE_APP_TAB_IDS)
    }
  }

  function 设置标签页可见(id: AppTabId, visible: boolean) {
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
      应用偏好(
        orderedTabIds.value,
        orderedTabIds.value.filter((tabId) => visibleSet.has(tabId)),
      )
      保存偏好()
      return true
    }

    if (REQUIRED_APP_TAB_IDS.includes(id) || visibleTabIds.value.length <= MIN_VISIBLE_TAB_COUNT) {
      return false
    }

    应用偏好(
      orderedTabIds.value,
      visibleTabIds.value.filter((tabId) => tabId !== id),
    )
    保存偏好()
    return true
  }

  function 移动标签页(id: AppTabId, direction: -1 | 1) {
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

    应用偏好(nextOrderedTabIds, visibleTabIds.value)
    保存偏好()
    return true
  }

  return {
    orderedTabIds,
    visibleTabIds,
    visibleTabs,
    settingsItems,
    minimumVisibleTabCount: MIN_VISIBLE_TAB_COUNT,
    maximumVisibleTabCount: MAX_VISIBLE_TAB_COUNT,
    init: 初始化,
    setTabVisible: 设置标签页可见,
    moveTab: 移动标签页,
  }
})
