import type { Pinia } from 'pinia'
import type { Router } from 'vue-router'
import { configureAuthStoreContext } from '@personal-system/domain/auth'
import { useAuthStore } from '../modules/auth/store'
import { configureApiClientContext } from '../shared/api/context'
import { initializeNativeShell } from './native-shell'
import { useApiEnvironmentStore } from '../shared/stores/api-environment'
import { useBlogAppearanceStore } from '../modules/blog/store'
import { useSettingsStore } from '../shared/stores/settings'
import { useThemeStore } from '../shared/stores/theme'
import { loginByDeveloperShortcut } from '../modules/auth/dev-login'

let appBootstrapTask: Promise<void> | null = null

export function initializeAppShell(pinia: Pinia, router: Router): Promise<void> {
  if (appBootstrapTask) {
    return appBootstrapTask
  }

  appBootstrapTask = (async () => {
    const theme = useThemeStore(pinia)
    const settings = useSettingsStore(pinia)
    const auth = useAuthStore(pinia)
    const apiEnvironment = useApiEnvironmentStore(pinia)
    const blogAppearance = useBlogAppearanceStore(pinia)

    theme.initTheme()
    theme.initHue()
    theme.listenToSystemTheme()
    blogAppearance.init()
    apiEnvironment.init()
    configureApiClientContext({
      getActiveBaseUrl: () => apiEnvironment.activeBaseUrl,
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      performDeveloperLogin: import.meta.env.DEV ? loginByDeveloperShortcut : undefined,
    })
    await initializeNativeShell(pinia, router)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })()

  return appBootstrapTask
}
