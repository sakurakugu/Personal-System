import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { 获取公开设置 as 请求获取公开设置 } from './api'
import { DEFAULT_PUBLIC_SETTINGS, type CommentVisibilityMode, type PublicSettings } from './types'

export const 使用设置存储 = defineStore('settings', () => {
  const settings = ref<PublicSettings>({ ...DEFAULT_PUBLIC_SETTINGS })
  const loaded = ref(false)
  let fetchTask: Promise<void> | null = null

  const registerEnabled = computed(() => {
    // 公开设置未返回前，统一按关闭注册处理，避免前端提前暴露注册入口。
    return loaded.value && settings.value.register_enabled === true
  })
  const commentsEnabled = computed(() => settings.value.comments_enabled !== false)
  const commentsHidden = computed(() => settings.value.comments_hidden === true)
  const commentVisibility = computed<CommentVisibilityMode>(() => {
    if (commentsHidden.value) {
      return 'hidden'
    }
    return commentsEnabled.value ? 'enabled' : 'closed'
  })

  async function fetchPublicSettings() {
    try {
      const data = await 请求获取公开设置()
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
    commentsEnabled,
    commentsHidden,
    commentVisibility,
    fetchPublicSettings,
    ensurePublicSettingsLoaded,
  }
})
