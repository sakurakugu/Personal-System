import { initializeThemeStore, runBootstrapTaskOnce } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import { configureApiClientContext } from '@personal-system/api'
import {
  configureAuthStoreContext,
  createDeviceTokenSessionDriver,
  isDeveloperLoginEnabled,
  useAuthStore,
} from '@personal-system/domain/auth'
import { useSettingsStore } from '@personal-system/domain/system'
import { useThemeStore } from '../shared/stores/theme'
import { loginByDeveloperShortcut } from '../modules/认证/lib/dev-login'
import {
  getStoredDesktopAuthToken,
  initializeDesktopAuthTokenStorage,
  setStoredDesktopAuthToken,
} from '../shared/auth/device-token'
import { useApiEnvironmentStore } from '../shared/stores/api-environment'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function initializeAppShell(pinia: Pinia): Promise<void> {
  return runBootstrapTaskOnce(bootstrapState, async () => {
    const auth = useAuthStore(pinia)
    const settings = useSettingsStore(pinia)
    const apiEnvironment = useApiEnvironmentStore(pinia)
    const theme = useThemeStore(pinia)

    await initializeDesktopAuthTokenStorage()
    apiEnvironment.init()

    configureApiClientContext({
      getActiveBaseUrl: () => apiEnvironment.activeBaseUrl,
      getAuthToken: getStoredDesktopAuthToken,
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      sessionDriver: createDeviceTokenSessionDriver({
        deviceName: 'Personal System',
        deviceType: 'desktop',
        scope: 'full_client',
        clientVersion: '0.1.0',
        platform: navigator.platform || 'desktop',
        persistToken: setStoredDesktopAuthToken,
      }),
      performDeveloperLogin: isDeveloperLoginEnabled() ? loginByDeveloperShortcut : undefined,
    })

    initializeThemeStore(theme)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })
}
