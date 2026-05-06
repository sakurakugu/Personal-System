import { initializeThemeStore, runBootstrapTaskOnce } from '@personal-system/app-core'
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
  initializeDesktopAuthTokenStorage,
  setStoredDesktopAuthToken,
} from '../shared/auth/device-token'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function initializeAppShell(pinia: Pinia): Promise<void> {
  return runBootstrapTaskOnce(bootstrapState, async () => {
    const auth = useAuthStore(pinia)
    const theme = useThemeStore(pinia)

    await initializeDesktopAuthTokenStorage()

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

    initializeThemeStore(theme)

    await auth.restoreUserIfNeeded()
  })
}
