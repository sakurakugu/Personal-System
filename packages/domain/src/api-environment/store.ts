import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface ApiEnvironmentItem {
  id: string
  name: string
  baseUrl: string
}

interface CreateApiEnvironmentStoreOptions {
  storeId: string
  storageKeyCustom: string
  storageKeyActive: string
  getDefaultEnvironments: () => ApiEnvironmentItem[]
  getDefaultEnvironmentId: () => string
  isEnvironmentSwitchEnabled: () => boolean
}

export function normalizeApiEnvironmentBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function getPreferredEnvironment(items: ApiEnvironmentItem[], defaultId: string): ApiEnvironmentItem | undefined {
  return items.find((item) => item.id === defaultId) || items[0]
}

export function createApiEnvironmentStore(options: CreateApiEnvironmentStoreOptions) {
  return defineStore(options.storeId, () => {
    const environments = ref<ApiEnvironmentItem[]>(options.getDefaultEnvironments())
    const activeEnvironmentId = ref(options.getDefaultEnvironmentId())
    const initialized = ref(false)

    const activeEnvironment = computed(() => {
      return environments.value.find((item) => item.id === activeEnvironmentId.value)
        || getPreferredEnvironment(environments.value, options.getDefaultEnvironmentId())
    })

    const activeBaseUrl = computed(() => {
      if (activeEnvironment.value?.baseUrl) {
        return activeEnvironment.value.baseUrl
      }
      const fallbackEnvironment = getPreferredEnvironment(
        options.getDefaultEnvironments(),
        options.getDefaultEnvironmentId(),
      )
      return fallbackEnvironment?.baseUrl || ''
    })

    const canSwitchEnvironment = computed(() => options.isEnvironmentSwitchEnabled())

    function saveCustomEnvironments() {
      const defaults = options.getDefaultEnvironments()
      const customOnly = environments.value.filter((item) => {
        const matched = defaults.find((defaultItem) => defaultItem.id === item.id)
        if (!matched) {
          return true
        }
        return matched.name !== item.name || matched.baseUrl !== item.baseUrl
      })
      localStorage.setItem(options.storageKeyCustom, JSON.stringify(customOnly))
    }

    function saveActiveEnvironment() {
      localStorage.setItem(options.storageKeyActive, activeEnvironmentId.value)
    }

    function applyCustomEnvironments(customItems: ApiEnvironmentItem[]) {
      const defaults = options.getDefaultEnvironments()
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
      activeEnvironmentId.value = options.getDefaultEnvironmentId()

      const rawCustom = localStorage.getItem(options.storageKeyCustom)
      const rawActive = localStorage.getItem(options.storageKeyActive)

      if (rawCustom) {
        try {
          const parsed = JSON.parse(rawCustom) as ApiEnvironmentItem[]
          if (Array.isArray(parsed)) {
            applyCustomEnvironments(parsed.map((item) => ({
              id: item.id,
              name: item.name,
              baseUrl: normalizeApiEnvironmentBaseUrl(item.baseUrl),
            })))
          }
        } catch {
          environments.value = options.getDefaultEnvironments()
        }
      }

      if (options.isEnvironmentSwitchEnabled() && rawActive && environments.value.some((item) => item.id === rawActive)) {
        activeEnvironmentId.value = rawActive
        return
      }

      const preferredEnvironment = getPreferredEnvironment(environments.value, options.getDefaultEnvironmentId())
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
        baseUrl: normalizeApiEnvironmentBaseUrl(baseUrl),
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
        baseUrl: normalizeApiEnvironmentBaseUrl(baseUrl),
      }
      environments.value = [
        ...environments.value.slice(0, index),
        updated,
        ...environments.value.slice(index + 1),
      ]
      saveCustomEnvironments()
    }

    function removeEnvironment(id: string) {
      if (options.getDefaultEnvironments().some((item) => item.id === id)) {
        return
      }
      environments.value = environments.value.filter((item) => item.id !== id)
      if (activeEnvironmentId.value === id) {
        const preferredEnvironment = getPreferredEnvironment(environments.value, options.getDefaultEnvironmentId())
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
}
