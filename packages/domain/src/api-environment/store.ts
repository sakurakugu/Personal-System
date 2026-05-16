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

export function 规范化API环境基础URL(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function 获取首选环境(items: ApiEnvironmentItem[], defaultId: string): ApiEnvironmentItem | undefined {
  return items.find((item) => item.id === defaultId) || items[0]
}

export function 创建API环境存储(options: CreateApiEnvironmentStoreOptions) {
  return defineStore(options.storeId, () => {
    const environments = ref<ApiEnvironmentItem[]>(options.getDefaultEnvironments())
    const activeEnvironmentId = ref(options.getDefaultEnvironmentId())
    const initialized = ref(false)

    const activeEnvironment = computed(() => {
      return environments.value.find((item) => item.id === activeEnvironmentId.value)
        || 获取首选环境(environments.value, options.getDefaultEnvironmentId())
    })

    const activeBaseUrl = computed(() => {
      if (activeEnvironment.value?.baseUrl) {
        return activeEnvironment.value.baseUrl
      }
      const fallbackEnvironment = 获取首选环境(
        options.getDefaultEnvironments(),
        options.getDefaultEnvironmentId(),
      )
      return fallbackEnvironment?.baseUrl || ''
    })

    const canSwitchEnvironment = computed(() => options.isEnvironmentSwitchEnabled())

    function 保存自定义环境() {
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

    function 保存活动环境() {
      localStorage.setItem(options.storageKeyActive, activeEnvironmentId.value)
    }

    function 应用自定义环境(customItems: ApiEnvironmentItem[]) {
      const defaults = options.getDefaultEnvironments()
      const customMap = new Map(customItems.map((item) => [item.id, item]))
      const mergedDefaults = defaults.map((item) => customMap.get(item.id) || item)
      const customOnly = customItems.filter((item) => !defaults.some((defaultItem) => defaultItem.id === item.id))
      environments.value = [...mergedDefaults, ...customOnly]
    }

    function 初始化() {
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
            应用自定义环境(parsed.map((item) => ({
              id: item.id,
              name: item.name,
              baseUrl: 规范化API环境基础URL(item.baseUrl),
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

      const preferredEnvironment = 获取首选环境(environments.value, options.getDefaultEnvironmentId())
      if (preferredEnvironment) {
        activeEnvironmentId.value = preferredEnvironment.id
      }
    }

    function 设置活动环境(id: string) {
      if (!environments.value.some((item) => item.id === id)) {
        return
      }
      activeEnvironmentId.value = id
      保存活动环境()
    }

    function 添加环境(name: string, baseUrl: string) {
      const newItem: ApiEnvironmentItem = {
        id: `custom-${Date.now()}`,
        name: name.trim(),
        baseUrl: 规范化API环境基础URL(baseUrl),
      }
      environments.value = [...environments.value, newItem]
      保存自定义环境()
      设置活动环境(newItem.id)
    }

    function 更新环境(id: string, name: string, baseUrl: string) {
      const index = environments.value.findIndex((item) => item.id === id)
      if (index < 0) {
        return
      }
      const updated: ApiEnvironmentItem = {
        ...environments.value[index],
        name: name.trim(),
        baseUrl: 规范化API环境基础URL(baseUrl),
      }
      environments.value = [
        ...environments.value.slice(0, index),
        updated,
        ...environments.value.slice(index + 1),
      ]
      保存自定义环境()
    }

    function 移除环境(id: string) {
      if (options.getDefaultEnvironments().some((item) => item.id === id)) {
        return
      }
      environments.value = environments.value.filter((item) => item.id !== id)
      if (activeEnvironmentId.value === id) {
        const preferredEnvironment = 获取首选环境(environments.value, options.getDefaultEnvironmentId())
        if (preferredEnvironment) {
          activeEnvironmentId.value = preferredEnvironment.id
        }
        保存活动环境()
      }
      保存自定义环境()
    }

    return {
      environments,
      activeEnvironmentId,
      activeEnvironment,
      activeBaseUrl,
      canSwitchEnvironment,
      初始化,
      setActiveEnvironment: 设置活动环境,
      addEnvironment: 添加环境,
      updateEnvironment: 更新环境,
      removeEnvironment: 移除环境,
    }
  })
}
