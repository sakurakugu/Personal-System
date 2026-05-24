import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'
import { Keyboard, KeyboardResize } from '@capacitor/keyboard'
import { StatusBar, Style } from '@capacitor/status-bar'
import type { Router } from 'vue-router'

let nativeShellTask: Promise<void> | null = null

export function 是否为原生应用(): boolean {
  return Capacitor.isNativePlatform()
}

export async function 同步原生主题(isDark: boolean): Promise<void> {
  if (!是否为原生应用()) {
    return
  }

  try {
    await StatusBar.setStyle({ style: isDark ? Style.Dark : Style.Light })
    await StatusBar.setBackgroundColor({ color: isDark ? '#171717' : '#fff9f2' })
    await StatusBar.setOverlaysWebView({ overlay: false })
  } catch {
    // 平台不支持时保持默认行为
  }
}

export function 初始化原生外壳(router: Router): Promise<void> {
  if (!是否为原生应用()) {
    return Promise.resolve()
  }

  if (nativeShellTask) {
    return nativeShellTask
  }

  nativeShellTask = (async () => {
    try {
      await Keyboard.setResizeMode({ mode: KeyboardResize.Body })
    } catch {
      // 不支持键盘尺寸调整的平台直接跳过
    }

    await App.addListener('backButton', ({ canGoBack }) => {
      const { path } = router.currentRoute.value

      if (path === '/') {
        void App.exitApp()
        return
      }

      if (canGoBack || window.history.length > 1) {
        router.back()
        return
      }

      void router.push('/')
    })
  })()

  return nativeShellTask
}
