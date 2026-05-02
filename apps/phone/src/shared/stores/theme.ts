import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  applyThemeHueToRoot,
  parseStoredHue,
  type OklchColorToken,
} from '@personal-system/theme'

type ThemeMode = 'light' | 'dark' | 'system'

const DEFAULT_HUE = 70
const PHONE_PRIMARY_RGB_TOKEN: OklchColorToken = { lightness: 0.72, chroma: 0.15 }

function applyHue(hueValue: number) {
  return applyThemeHueToRoot({
    hueValue,
    primaryRgbToken: PHONE_PRIMARY_RGB_TOKEN,
  })
}

export const useThemeStore = defineStore('phone-theme', () => {
  const mode = ref<ThemeMode>('system')
  const isDark = ref(false)
  const hue = ref(DEFAULT_HUE)
  let mediaQuery: MediaQueryList | null = null

  const modeLabel = computed(() => {
    if (mode.value === 'system') {
      return '跟随系统'
    }
    return mode.value === 'dark' ? '深色模式' : '浅色模式'
  })

  function resolveSystemDark() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  function applyTheme() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  function syncThemeFromMode() {
    isDark.value = mode.value === 'system' ? resolveSystemDark() : mode.value === 'dark'
    applyTheme()
  }

  function initTheme() {
    const savedMode = localStorage.getItem('theme')
    if (savedMode === 'light' || savedMode === 'dark' || savedMode === 'system') {
      mode.value = savedMode
    } else {
      mode.value = 'system'
      localStorage.setItem('theme', 'system')
    }
    syncThemeFromMode()
  }

  function setMode(nextMode: ThemeMode) {
    mode.value = nextMode
    localStorage.setItem('theme', nextMode)
    syncThemeFromMode()
  }

  function handleSystemThemeChange(event: MediaQueryListEvent) {
    if (mode.value !== 'system') {
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

  function initHue() {
    const savedHue = localStorage.getItem('hue')
    hue.value = parseStoredHue(savedHue, DEFAULT_HUE)
    applyHue(hue.value)
  }

  function setHue(value: number) {
    const nextHue = applyHue(value)
    hue.value = nextHue
    localStorage.setItem('hue', String(nextHue))
  }

  return {
    mode,
    isDark,
    hue,
    defaultHue: DEFAULT_HUE,
    modeLabel,
    initTheme,
    setMode,
    listenToSystemTheme,
    initHue,
    setHue,
  }
})
