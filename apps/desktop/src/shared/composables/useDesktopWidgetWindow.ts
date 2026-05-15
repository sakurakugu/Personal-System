import { readonly, ref } from 'vue'
import {
  closeDesktopWidgetWindow,
  getDesktopWidgetWindowState,
  onDesktopWidgetWindowStateChange,
  openDesktopWidgetWindow,
} from '@/shared/window-manager'

const isDesktopWidgetWindowOpen = ref(false)

let initialized = false
let initializePromise: Promise<void> | null = null
let removeWidgetStateListener = () => {}
let pageLifecycleListenersBound = false

async function syncDesktopWidgetWindowState() {
  try {
    const state = await getDesktopWidgetWindowState()
    isDesktopWidgetWindowOpen.value = state.open
  } catch (error) {
    console.error('读取桌面小工具状态失败', error)
  }
}

function bindPageLifecycleListeners() {
  if (pageLifecycleListenersBound || typeof window === 'undefined' || typeof document === 'undefined') {
    return
  }

  const handleWindowFocus = () => {
    void syncDesktopWidgetWindowState()
  }
  const handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      void syncDesktopWidgetWindowState()
    }
  }

  window.addEventListener('focus', handleWindowFocus)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  pageLifecycleListenersBound = true
}

async function ensureDesktopWidgetWindowState() {
  if (initialized) {
    return
  }

  if (!initializePromise) {
    initializePromise = (async () => {
      removeWidgetStateListener()
      removeWidgetStateListener = onDesktopWidgetWindowStateChange((payload) => {
        isDesktopWidgetWindowOpen.value = payload.open
      })
      bindPageLifecycleListeners()
      await syncDesktopWidgetWindowState()
      initialized = true
    })().finally(() => {
      initializePromise = null
    })
  }

  await initializePromise
}

export function useDesktopWidgetWindow() {
  void ensureDesktopWidgetWindowState()

  async function toggleDesktopWidgetWindow() {
    await ensureDesktopWidgetWindowState()

    if (isDesktopWidgetWindowOpen.value) {
      await closeDesktopWidgetWindow()
      isDesktopWidgetWindowOpen.value = false
      return
    }

    await openDesktopWidgetWindow()
    isDesktopWidgetWindowOpen.value = true
  }

  return {
    isDesktopWidgetWindowOpen: readonly(isDesktopWidgetWindowOpen),
    toggleDesktopWidgetWindow,
    syncDesktopWidgetWindowState,
  }
}
