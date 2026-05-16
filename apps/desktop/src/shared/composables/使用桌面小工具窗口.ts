import { readonly, ref } from 'vue'
import {
  关闭桌面小工具窗口,
  获取桌面小工具窗口状态,
  监听桌面小工具窗口状态变更,
  打开桌面小工具窗口,
} from '@/shared/window-manager'

const isDesktopWidgetWindowOpen = ref(false)

let initialized = false
let initializePromise: Promise<void> | null = null
let removeWidgetStateListener = () => {}
let pageLifecycleListenersBound = false

async function 同步桌面小工具窗口状态() {
  try {
    const state = await 获取桌面小工具窗口状态()
    isDesktopWidgetWindowOpen.value = state.open
  } catch (error) {
    console.error('读取桌面小工具状态失败', error)
  }
}

function 绑定页面生命周期监听器() {
  if (pageLifecycleListenersBound || typeof window === 'undefined' || typeof document === 'undefined') {
    return
  }

  const handleWindowFocus = () => {
    void 同步桌面小工具窗口状态()
  }
  const handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      void 同步桌面小工具窗口状态()
    }
  }

  window.addEventListener('focus', handleWindowFocus)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  pageLifecycleListenersBound = true
}

async function 确保桌面小工具窗口状态() {
  if (initialized) {
    return
  }

  if (!initializePromise) {
    initializePromise = (async () => {
      removeWidgetStateListener()
      removeWidgetStateListener = 监听桌面小工具窗口状态变更((payload) => {
        isDesktopWidgetWindowOpen.value = payload.open
      })
      绑定页面生命周期监听器()
      await 同步桌面小工具窗口状态()
      initialized = true
    })().finally(() => {
      initializePromise = null
    })
  }

  await initializePromise
}

export function 使用桌面小工具窗口() {
  void 确保桌面小工具窗口状态()

  async function toggleDesktopWidgetWindow() {
    await 确保桌面小工具窗口状态()

    if (isDesktopWidgetWindowOpen.value) {
      await 关闭桌面小工具窗口()
      isDesktopWidgetWindowOpen.value = false
      return
    }

    await 打开桌面小工具窗口()
    isDesktopWidgetWindowOpen.value = true
  }

  return {
    isDesktopWidgetWindowOpen: readonly(isDesktopWidgetWindowOpen),
    toggleDesktopWidgetWindow,
    同步桌面小工具窗口状态,
  }
}
