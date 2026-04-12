import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)
  const followSystem = ref(false)
  const clickEffectEnabled = ref(true)
  let mediaQuery: MediaQueryList | null = null

  function initTheme() {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark') {
      isDark.value = true
      followSystem.value = false
    } else if (saved === 'light') {
      isDark.value = false
      followSystem.value = false
    } else if (saved === 'system') {
      // 跟随系统
      followSystem.value = true
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    } else {
      // 默认跟随系统
      followSystem.value = true
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
      localStorage.setItem('theme', 'system')
    }
    applyTheme()

    const savedClickEffect = localStorage.getItem('clickEffectEnabled')
    clickEffectEnabled.value = savedClickEffect !== 'false'
  }

  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // 切换主题（仅在非跟随系统模式下有效）
  function toggleTheme() {
    if (followSystem.value) {
      // 如果正在跟随系统，切换为手动模式并设置相反的主题
      followSystem.value = false
      isDark.value = !isDark.value
      localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    } else {
      isDark.value = !isDark.value
      localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    }
    applyTheme()
  }

  function setFollowSystem(value: boolean | string | number) {
    const boolValue = Boolean(value)
    followSystem.value = boolValue
    if (boolValue) {
      localStorage.setItem('theme', 'system')
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    } else {
      localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    }
    applyTheme()
  }

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    if (!followSystem.value) {
      return
    }
    isDark.value = event.matches
    applyTheme()
  }

  function listenToSystemTheme() {
    if (mediaQuery) {
      return
    }
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', handleSystemThemeChange)
  }

  const modeLabel = computed(() => {
    if (followSystem.value) return '跟随系统'
    return isDark.value ? '深色模式' : '浅色模式'
  })

  function setClickEffectEnabled(value: boolean | string | number) {
    clickEffectEnabled.value = Boolean(value)
    localStorage.setItem('clickEffectEnabled', String(Boolean(value)))
  }

  return {
    isDark,
    followSystem,
    clickEffectEnabled,
    modeLabel,
    initTheme,
    toggleTheme,
    setFollowSystem,
    applyTheme,
    listenToSystemTheme,
    setClickEffectEnabled,
  }
})
