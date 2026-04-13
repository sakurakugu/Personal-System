import type { Pinia } from 'pinia'
import type { Router } from 'vue-router'
import { initializeNativeShell } from './native-shell'
import { useApiEnvironmentStore } from '../stores/api-environment'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { useThemeStore } from '../stores/theme'

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

    theme.initTheme()
    theme.initHue()
    theme.listenToSystemTheme()
    apiEnvironment.init()
    await initializeNativeShell(pinia, router)

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })()

  return appBootstrapTask
}
