import {
  applyThemeHueToRoot,
  DEFAULT_THEME_HUE,
  DEFAULT_THEME_PRIMARY_RGB_TOKEN,
  getThemeModeLabel,
  parseStoredHue,
  parseStoredThemeMode,
  resolveIsDarkFromMode,
  resolveSystemDark,
  type ThemeMode,
} from '@personal-system/theme'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const DEFAULT_HUE = DEFAULT_THEME_HUE

function applyHue(hueValue: number) {
  return applyThemeHueToRoot({
    hueValue,
    primaryRgbToken: DEFAULT_THEME_PRIMARY_RGB_TOKEN,
  })
}

export const useThemeStore = defineStore('desktop-theme', () => {
  const mode = ref<ThemeMode>('system')
  const isDark = ref(false)
  const hue = ref(DEFAULT_HUE)
  let mediaQuery: MediaQueryList | null = null

  const modeLabel = computed(() => getThemeModeLabel(mode.value))

  function applyTheme() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  function syncThemeFromMode() {
    isDark.value = resolveIsDarkFromMode(mode.value, resolveSystemDark())
    applyTheme()
  }

  function initTheme() {
    mode.value = parseStoredThemeMode(localStorage.getItem('theme'))
    localStorage.setItem('theme', mode.value)
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
    hue.value = parseStoredHue(localStorage.getItem('hue'), DEFAULT_HUE)
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
