import type { Pinia } from 'pinia'
import { configureAuthStoreContext, isDeveloperLoginEnabled, useAuthStore } from '@personal-system/domain/auth'
import { configureApiClientContext } from '@personal-system/api'
import { useSettingsStore } from '@personal-system/domain/system'
import type { Router } from 'vue-router'
import { initializeNativeShell } from './native-shell'
import { loginByDeveloperShortcut } from '../auth/dev-login'
import { useApiEnvironmentStore } from '../stores/api-environment'

let appBootstrapTask: Promise<void> | null = null

export function initializeAppShell(pinia: Pinia, router: Router): Promise<void> {
  if (appBootstrapTask) {
    return appBootstrapTask
  }

  appBootstrapTask = (async () => {
    const auth = useAuthStore(pinia)
    const settings = useSettingsStore(pinia)
    const apiEnvironment = useApiEnvironmentStore(pinia)

    configureApiClientContext({
      getActiveBaseUrl: () => apiEnvironment.activeBaseUrl,
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      performDeveloperLogin: isDeveloperLoginEnabled() ? loginByDeveloperShortcut : undefined,
    })
    apiEnvironment.init()
    await initializeNativeShell(router)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })()

  return appBootstrapTask
}
