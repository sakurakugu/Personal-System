import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

type ThemeMode = 'light' | 'dark' | 'system'

const DEFAULT_HUE = 70

function clampHue(value: number) {
  if (Number.isNaN(value)) {
    return DEFAULT_HUE
  }
  const normalized = ((Math.round(value) % 360) + 360) % 360
  return normalized
}

function hslToRgb(hue: number, saturation: number, lightness: number) {
  const normalizedHue = ((hue % 360) + 360) % 360
  const s = saturation / 100
  const l = lightness / 100
  const chroma = (1 - Math.abs(2 * l - 1)) * s
  const hueSection = normalizedHue / 60
  const x = chroma * (1 - Math.abs(hueSection % 2 - 1))

  let red = 0
  let green = 0
  let blue = 0

  if (hueSection >= 0 && hueSection < 1) {
    red = chroma
    green = x
  } else if (hueSection < 2) {
    red = x
    green = chroma
  } else if (hueSection < 3) {
    green = chroma
    blue = x
  } else if (hueSection < 4) {
    green = x
    blue = chroma
  } else if (hueSection < 5) {
    red = x
    blue = chroma
  } else {
    red = chroma
    blue = x
  }

  const match = l - chroma / 2

  return [
    Math.round((red + match) * 255),
    Math.round((green + match) * 255),
    Math.round((blue + match) * 255),
  ]
}

function applyHue(hueValue: number) {
  const root = document.documentElement
  root.style.setProperty('--hue', String(hueValue))
  root.style.setProperty('--selection-hue', String(hueValue))
  root.style.setProperty('--el-color-primary-rgb', hslToRgb(hueValue, 72, 54).join(', '))
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
    const parsed = savedHue ? Number.parseInt(savedHue, 10) : NaN
    hue.value = clampHue(parsed)
    applyHue(hue.value)
  }

  function setHue(value: number) {
    const nextHue = clampHue(value)
    hue.value = nextHue
    localStorage.setItem('hue', String(nextHue))
    applyHue(nextHue)
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
