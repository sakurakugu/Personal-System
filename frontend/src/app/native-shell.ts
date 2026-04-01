import type { Pinia } from 'pinia'
import type { Router } from 'vue-router'
import { watch } from 'vue'
import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'
import { Keyboard, KeyboardResize } from '@capacitor/keyboard'
import { StatusBar, Style } from '@capacitor/status-bar'
import { useThemeStore } from '../stores/theme'

let nativeShellTask: Promise<void> | null = null

export function isNativeApp(): boolean {
  return Capacitor.isNativePlatform()
}

export function initializeNativeShell(pinia: Pinia, router: Router): Promise<void> {
  if (!isNativeApp()) {
    return Promise.resolve()
  }

  if (nativeShellTask) {
    return nativeShellTask
  }

  nativeShellTask = (async () => {
    const theme = useThemeStore(pinia)

    const syncStatusBar = async () => {
      try {
        await StatusBar.setStyle({ style: theme.isDark ? Style.Dark : Style.Light })
        await StatusBar.setBackgroundColor({ color: theme.isDark ? '#1e293b' : '#ffffff' })
      } catch {
        // 某些平台或 Web 环境下状态栏能力不可用，静默跳过
      }
    }

    try {
      await StatusBar.setOverlaysWebView({ overlay: false })
    } catch {
      // 平台不支持时保持默认行为
    }

    try {
      await Keyboard.setResizeMode({ mode: KeyboardResize.Body })
    } catch {
      // 不支持键盘尺寸调整的平台直接跳过
    }

    await syncStatusBar()

    watch(() => theme.isDark, () => {
      void syncStatusBar()
    })

    await App.addListener('backButton', ({ canGoBack }) => {
      const { path } = router.currentRoute.value

      if (path === '/blog') {
        void App.exitApp()
        return
      }

      if (canGoBack || window.history.length > 1) {
        router.back()
        return
      }

      void router.push('/blog')
    })
  })()

  return nativeShellTask
}
