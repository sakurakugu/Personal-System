import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchPublicSettings as requestPublicSettings } from '../../modules/system/api'
import { DEFAULT_PUBLIC_SETTINGS, type PublicSettings } from '../../modules/system/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<PublicSettings>({ ...DEFAULT_PUBLIC_SETTINGS })
  const loaded = ref(false)
  let fetchTask: Promise<void> | null = null

  const registerEnabled = computed(() => settings.value.register_enabled)

  async function fetchPublicSettings() {
    try {
      const data = await requestPublicSettings()
      settings.value = { ...settings.value, ...data }
    } catch {
      // 保持默认值，避免公开页面因接口失败而阻塞。
    } finally {
      loaded.value = true
    }
  }

  function ensurePublicSettingsLoaded(): Promise<void> {
    if (loaded.value) {
      return Promise.resolve()
    }
    if (fetchTask) {
      return fetchTask
    }
    fetchTask = fetchPublicSettings().finally(() => {
      fetchTask = null
    })
    return fetchTask
  }

  return {
    settings,
    loaded,
    registerEnabled,
    fetchPublicSettings,
    ensurePublicSettingsLoaded,
  }
})
