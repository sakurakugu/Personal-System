import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { Capacitor } from '@capacitor/core'
import { isApiEnvironmentSwitchEnabled, isNativeDevServerMode, resolveNativeDevServerApiBase } from '@personal-system/api'

export interface ApiEnvironmentItem {
  id: string
  name: string
  baseUrl: string
}

const STORAGE_KEY_CUSTOM = 'personal-system:api-env:custom'
const STORAGE_KEY_ACTIVE = 'personal-system:api-env:active'
const DEFAULT_SERVER_ENVIRONMENT_ID = 'server'
const DEFAULT_LOCAL_ENVIRONMENT_ID = 'local'
const DEFAULT_SERVER_API_BASE = 'https://api.sakurakugu.top/v1'
const DEFAULT_ANDROID_LOCAL_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_LOCAL_API_BASE = 'http://127.0.0.1:8000/api/v1'

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function getDefaultLocalApiBase(): string {
  if (isNativeDevServerMode()) {
    return normalizeBaseUrl(resolveNativeDevServerApiBase())
  }
  if (Capacitor.getPlatform() === 'android') {
    return DEFAULT_ANDROID_LOCAL_API_BASE
  }
  return DEFAULT_IOS_LOCAL_API_BASE
}

function getDefaultEnvironmentId(): string {
  if (import.meta.env.DEV) {
    return DEFAULT_LOCAL_ENVIRONMENT_ID
  }
  return DEFAULT_SERVER_ENVIRONMENT_ID
}

function getDefaultEnvironments(): ApiEnvironmentItem[] {
  const serverBase =
    import.meta.env.VITE_SERVER_API_BASE?.trim()
    || import.meta.env.VITE_PRODUCTION_API_BASE?.trim()
    || DEFAULT_SERVER_API_BASE

  return [
    { id: DEFAULT_SERVER_ENVIRONMENT_ID, name: '线上环境', baseUrl: normalizeBaseUrl(serverBase) },
    { id: DEFAULT_LOCAL_ENVIRONMENT_ID, name: '本地开发', baseUrl: normalizeBaseUrl(getDefaultLocalApiBase()) },
  ]
}

function isDefaultEnvironment(id: string): boolean {
  return getDefaultEnvironments().some((item) => item.id === id)
}

function getPreferredEnvironment(items: ApiEnvironmentItem[]): ApiEnvironmentItem | undefined {
  const defaultId = getDefaultEnvironmentId()
  return items.find((item) => item.id === defaultId) || items[0]
}

export const useApiEnvironmentStore = defineStore('phone-api-environment', () => {
  const environments = ref<ApiEnvironmentItem[]>(getDefaultEnvironments())
  const activeEnvironmentId = ref(getDefaultEnvironmentId())
  const initialized = ref(false)

  const activeEnvironment = computed(() => {
    return environments.value.find((item) => item.id === activeEnvironmentId.value) || getPreferredEnvironment(environments.value)
  })

  const activeBaseUrl = computed(() => {
    if (activeEnvironment.value?.baseUrl) {
      return activeEnvironment.value.baseUrl
    }
    if (getDefaultEnvironmentId() === DEFAULT_LOCAL_ENVIRONMENT_ID) {
      return normalizeBaseUrl(getDefaultLocalApiBase())
    }
    return normalizeBaseUrl(DEFAULT_SERVER_API_BASE)
  })

  const canSwitchEnvironment = computed(() => isApiEnvironmentSwitchEnabled())

  function saveCustomEnvironments() {
    const defaults = getDefaultEnvironments()
    const customOnly = environments.value.filter((item) => {
      const matched = defaults.find((defaultItem) => defaultItem.id === item.id)
      if (!matched) {
        return true
      }
      return matched.name !== item.name || matched.baseUrl !== item.baseUrl
    })
    localStorage.setItem(STORAGE_KEY_CUSTOM, JSON.stringify(customOnly))
  }

  function saveActiveEnvironment() {
    localStorage.setItem(STORAGE_KEY_ACTIVE, activeEnvironmentId.value)
  }

  function applyCustomEnvironments(customItems: ApiEnvironmentItem[]) {
    const defaults = getDefaultEnvironments()
    const customMap = new Map(customItems.map((item) => [item.id, item]))
    const mergedDefaults = defaults.map((item) => customMap.get(item.id) || item)
    const customOnly = customItems.filter((item) => !defaults.some((defaultItem) => defaultItem.id === item.id))
    environments.value = [...mergedDefaults, ...customOnly]
  }

  function init() {
    if (initialized.value) {
      return
    }
    initialized.value = true
    activeEnvironmentId.value = getDefaultEnvironmentId()

    const rawCustom = localStorage.getItem(STORAGE_KEY_CUSTOM)
    const rawActive = localStorage.getItem(STORAGE_KEY_ACTIVE)

    if (rawCustom) {
      try {
        const parsed = JSON.parse(rawCustom) as ApiEnvironmentItem[]
        if (Array.isArray(parsed)) {
          applyCustomEnvironments(parsed.map((item) => ({
            id: item.id,
            name: item.name,
            baseUrl: normalizeBaseUrl(item.baseUrl),
          })))
        }
      } catch {
        environments.value = getDefaultEnvironments()
      }
    }

    if (isApiEnvironmentSwitchEnabled() && rawActive && environments.value.some((item) => item.id === rawActive)) {
      activeEnvironmentId.value = rawActive
      return
    }

    const preferredEnvironment = getPreferredEnvironment(environments.value)
    if (preferredEnvironment) {
      activeEnvironmentId.value = preferredEnvironment.id
    }
  }

  function setActiveEnvironment(id: string) {
    if (!environments.value.some((item) => item.id === id)) {
      return
    }
    activeEnvironmentId.value = id
    saveActiveEnvironment()
  }

  function addEnvironment(name: string, baseUrl: string) {
    const newItem: ApiEnvironmentItem = {
      id: `custom-${Date.now()}`,
      name: name.trim(),
      baseUrl: normalizeBaseUrl(baseUrl),
    }
    environments.value = [...environments.value, newItem]
    saveCustomEnvironments()
    setActiveEnvironment(newItem.id)
  }

  function updateEnvironment(id: string, name: string, baseUrl: string) {
    const index = environments.value.findIndex((item) => item.id === id)
    if (index < 0) {
      return
    }
    const updated: ApiEnvironmentItem = {
      ...environments.value[index],
      name: name.trim(),
      baseUrl: normalizeBaseUrl(baseUrl),
    }
    environments.value = [
      ...environments.value.slice(0, index),
      updated,
      ...environments.value.slice(index + 1),
    ]
    saveCustomEnvironments()
  }

  function removeEnvironment(id: string) {
    if (isDefaultEnvironment(id)) {
      return
    }
    environments.value = environments.value.filter((item) => item.id !== id)
    if (activeEnvironmentId.value === id) {
      const preferredEnvironment = getPreferredEnvironment(environments.value)
      if (preferredEnvironment) {
        activeEnvironmentId.value = preferredEnvironment.id
      }
      saveActiveEnvironment()
    }
    saveCustomEnvironments()
  }

  return {
    environments,
    activeEnvironmentId,
    activeEnvironment,
    activeBaseUrl,
    canSwitchEnvironment,
    init,
    setActiveEnvironment,
    addEnvironment,
    updateEnvironment,
    removeEnvironment,
  }
})
