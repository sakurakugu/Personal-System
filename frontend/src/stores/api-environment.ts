import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { Capacitor } from '@capacitor/core'

export interface ApiEnvironmentItem {
  id: string
  name: string
  baseUrl: string
}

const STORAGE_KEY_CUSTOM = 'web-system:api-env:custom'
const STORAGE_KEY_ACTIVE = 'web-system:api-env:active'
const DEFAULT_SERVER_API_BASE = 'https://api.sakurakugu.top/api/v1'
const DEFAULT_ANDROID_LOCAL_API_BASE = 'http://10.0.2.2:8000/api/v1'
const DEFAULT_IOS_LOCAL_API_BASE = 'http://127.0.0.1:8000/api/v1'

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function getDefaultLocalApiBase(): string {
  if (Capacitor.getPlatform() === 'android') {
    return DEFAULT_ANDROID_LOCAL_API_BASE
  }
  return DEFAULT_IOS_LOCAL_API_BASE
}

function getDefaultEnvironments(): ApiEnvironmentItem[] {
  const serverBase =
    import.meta.env.VITE_SERVER_API_BASE?.trim()
    || import.meta.env.VITE_PRODUCTION_API_BASE?.trim()
    || DEFAULT_SERVER_API_BASE

  return [
    { id: 'server', name: '线上环境', baseUrl: normalizeBaseUrl(serverBase) },
    { id: 'local', name: '本地开发', baseUrl: normalizeBaseUrl(getDefaultLocalApiBase()) },
  ]
}

function isDefaultEnvironment(id: string): boolean {
  return getDefaultEnvironments().some((item) => item.id === id)
}

export const useApiEnvironmentStore = defineStore('api-environment', () => {
  const environments = ref<ApiEnvironmentItem[]>(getDefaultEnvironments())
  const activeEnvironmentId = ref('server')
  const initialized = ref(false)

  const activeEnvironment = computed(() => {
    return environments.value.find((item) => item.id === activeEnvironmentId.value) || environments.value[0]
  })

  const activeBaseUrl = computed(() => activeEnvironment.value?.baseUrl || normalizeBaseUrl(DEFAULT_SERVER_API_BASE))

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

    if (rawActive && environments.value.some((item) => item.id === rawActive)) {
      activeEnvironmentId.value = rawActive
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
    if (activeEnvironmentId.value === id && environments.value.length > 0) {
      activeEnvironmentId.value = environments.value[0].id
      saveActiveEnvironment()
    }
    saveCustomEnvironments()
  }

  return {
    environments,
    activeEnvironmentId,
    activeEnvironment,
    activeBaseUrl,
    init,
    setActiveEnvironment,
    addEnvironment,
    updateEnvironment,
    removeEnvironment,
  }
})
