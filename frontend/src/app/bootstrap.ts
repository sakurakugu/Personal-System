import type { Pinia } from 'pinia'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { useThemeStore } from '../stores/theme'

let appBootstrapTask: Promise<void> | null = null

export function initializeAppShell(pinia: Pinia): Promise<void> {
  if (appBootstrapTask) {
    return appBootstrapTask
  }

  appBootstrapTask = (async () => {
    const theme = useThemeStore(pinia)
    const settings = useSettingsStore(pinia)
    const auth = useAuthStore(pinia)

    theme.initTheme()
    theme.listenToSystemTheme()

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })()

  return appBootstrapTask
}
