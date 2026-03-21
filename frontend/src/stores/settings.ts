import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../utils/api'

interface SystemSettings {
  comments_enabled: boolean
  comments_stealth: boolean
  comments_min_role: string
  register_enabled: boolean
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<SystemSettings>({
    comments_enabled: true,
    comments_stealth: false,
    comments_min_role: 'guest',
    register_enabled: true,
  })
  const loaded = ref(false)

  const registerEnabled = computed(() => settings.value.register_enabled)

  async function fetchPublicSettings() {
    try {
      const { data } = await api.get('/admin/public-settings')
      settings.value = { ...settings.value, ...data }
      loaded.value = true
    } catch {
      // 使用默认值
      loaded.value = true
    }
  }

  return {
    settings,
    loaded,
    registerEnabled,
    fetchPublicSettings,
  }
})
