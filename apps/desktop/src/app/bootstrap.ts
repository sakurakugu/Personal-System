import type { Pinia } from 'pinia'
import { configureApiClientContext } from '@personal-system/api'
import {
  configureAuthStoreContext,
  createDeviceTokenSessionDriver,
  useAuthStore,
} from '@personal-system/domain/auth'
import { useThemeStore } from '../shared/stores/theme'
import {
  getStoredDesktopAuthToken,
  setStoredDesktopAuthToken,
} from '../shared/auth/device-token'

let appBootstrapTask: Promise<void> | null = null

export function initializeAppShell(pinia: Pinia): Promise<void> {
  if (appBootstrapTask) {
    return appBootstrapTask
  }

  appBootstrapTask = (async () => {
    const auth = useAuthStore(pinia)
    const theme = useThemeStore(pinia)

    configureApiClientContext({
      getAuthToken: getStoredDesktopAuthToken,
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      sessionDriver: createDeviceTokenSessionDriver({
        deviceName: 'Personal System Desktop',
        deviceType: 'desktop',
        scope: 'full_client',
        clientVersion: '0.1.0',
        platform: navigator.platform || 'desktop',
        persistToken: setStoredDesktopAuthToken,
      }),
    })

    theme.initTheme()
    theme.initHue()
    theme.listenToSystemTheme()

    await auth.restoreUserIfNeeded()
  })()

  return appBootstrapTask
}
