import { initializeThemeStore, runBootstrapTaskOnce } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import {
  configureAuthStoreContext,
  createDeviceTokenSessionDriver,
  isDeveloperLoginEnabled,
  useAuthStore,
} from '@personal-system/domain/auth'
import { configureApiClientContext } from '@personal-system/api'
import { useSettingsStore } from '@personal-system/domain/system'
import type { Router } from 'vue-router'
import { watch } from 'vue'
import { initializeNativeShell, syncNativeTheme } from './native-shell'
import { loginByDeveloperShortcut } from '../modules/auth/lib/dev-login'
import {
  getStoredPhoneAuthToken,
  initializePhoneAuthTokenStorage,
  setStoredPhoneAuthToken,
} from '../shared/auth/device-token'
import { useApiEnvironmentStore } from '../shared/stores/api-environment'
import { useTabBarStore } from '../shared/stores/tab-bar'
import { useThemeStore } from '../shared/stores/theme'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function initializeAppShell(pinia: Pinia, router: Router): Promise<void> {
  return runBootstrapTaskOnce(bootstrapState, async () => {
    const auth = useAuthStore(pinia)
    const settings = useSettingsStore(pinia)
    const apiEnvironment = useApiEnvironmentStore(pinia)
    const tabBar = useTabBarStore(pinia)
    const theme = useThemeStore(pinia)

    await initializePhoneAuthTokenStorage()

    configureApiClientContext({
      getActiveBaseUrl: () => apiEnvironment.activeBaseUrl,
      getAuthToken: getStoredPhoneAuthToken,
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      sessionDriver: createDeviceTokenSessionDriver({
        deviceName: 'Personal System Phone',
        deviceType: 'phone',
        scope: 'full_client',
        platform: navigator.platform || 'phone',
        persistToken: setStoredPhoneAuthToken,
      }),
      performDeveloperLogin: isDeveloperLoginEnabled() ? loginByDeveloperShortcut : undefined,
    })
    initializeThemeStore(theme)
    tabBar.init()
    watch(
      () => theme.isDark,
      (isDark) => {
        void syncNativeTheme(isDark)
      },
      { immediate: true },
    )
    apiEnvironment.init()
    await initializeNativeShell(router)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })
}
