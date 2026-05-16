import {
  DEFAULT_THEME_HUE,
  DEFAULT_THEME_PRIMARY_RGB_TOKEN,
  应用主题色相到根元素,
  获取主题模式标签,
  解析存储的色相,
  解析存储的主题模式,
  从模式解析是否为暗色,
  解析系统暗色,
  type ThemeMode,
} from '@personal-system/theme'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const DEFAULT_HUE = DEFAULT_THEME_HUE

function 应用色相(hueValue: number) {
  return 应用主题色相到根元素({
    hueValue,
    primaryRgbToken: DEFAULT_THEME_PRIMARY_RGB_TOKEN,
  })
}

export const 使用主题存储 = defineStore('desktop-theme', () => {
  const mode = ref<ThemeMode>('system')
  const isDark = ref(false)
  const hue = ref(DEFAULT_HUE)
  let mediaQuery: MediaQueryList | null = null
  let storageListenerBound = false

  const modeLabel = computed(() => 获取主题模式标签(mode.value))

  function 应用主题() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  function 同步主题模式() {
    isDark.value = 从模式解析是否为暗色(mode.value, 解析系统暗色())
    应用主题()
  }

  function 初始化主题() {
    mode.value = 解析存储的主题模式(localStorage.getItem('theme'))
    localStorage.setItem('theme', mode.value)
    同步主题模式()
  }

  function 设置模式(nextMode: ThemeMode) {
    mode.value = nextMode
    localStorage.setItem('theme', nextMode)
    同步主题模式()
  }

  function 处理存储变更(event: StorageEvent) {
    if (event.storageArea !== localStorage) {
      return
    }

    if (event.key === 'theme') {
      const nextMode = 解析存储的主题模式(event.newValue)
      if (nextMode === mode.value) {
        return
      }
      mode.value = nextMode
      同步主题模式()
      return
    }

    if (event.key === 'hue') {
      const nextHue = 解析存储的色相(event.newValue, DEFAULT_HUE)
      if (nextHue === hue.value) {
        return
      }
      hue.value = nextHue
      应用色相(nextHue)
    }
  }

  function 处理系统主题变更(event: MediaQueryListEvent) {
    if (mode.value !== 'system') {
      return
    }
    isDark.value = event.matches
    应用主题()
  }

  function 监听系统主题() {
    if (mediaQuery) {
      return
    }
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', 处理系统主题变更)
    if (!storageListenerBound) {
      window.addEventListener('storage', 处理存储变更)
      storageListenerBound = true
    }
  }

  function 初始化色相() {
    hue.value = 解析存储的色相(localStorage.getItem('hue'), DEFAULT_HUE)
    应用色相(hue.value)
  }

  function 设置色相(value: number) {
    const nextHue = 应用色相(value)
    hue.value = nextHue
    localStorage.setItem('hue', String(nextHue))
  }

  return {
    mode,
    isDark,
    hue,
    defaultHue: DEFAULT_HUE,
    modeLabel,
    initTheme: 初始化主题,
    setMode: 设置模式,
    listenToSystemTheme: 监听系统主题,
    initHue: 初始化色相,
    setHue: 设置色相,
  }
})
