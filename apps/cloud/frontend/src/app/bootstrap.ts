import { initializeThemeStore, runBootstrapTaskOnce } from '@personal-system/app-core'
import type { Pinia } from 'pinia'
import { configureAuthStoreContext, useAuthStore } from '@personal-system/domain/auth'
import { configureApiClientContext } from '../shared/api/context'
import { useBlogAppearanceStore } from '../modules/博客/store'
import { useSettingsStore } from '../shared/stores/settings'
import { useThemeStore } from '../shared/stores/theme'
import { loginByDeveloperShortcut } from '../modules/认证/dev-login'

const bootstrapState = {
  task: null as Promise<void> | null,
}

export function initializeAppShell(pinia: Pinia): Promise<void> {
  return runBootstrapTaskOnce(bootstrapState, async () => {
    const theme = useThemeStore(pinia)
    const settings = useSettingsStore(pinia)
    const auth = useAuthStore(pinia)
    const blogAppearance = useBlogAppearanceStore(pinia)

    initializeThemeStore(theme)
    blogAppearance.init()
    configureApiClientContext({
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({
      performDeveloperLogin: import.meta.env.DEV ? loginByDeveloperShortcut : undefined,
    })

    await Promise.all([
      settings.ensurePublicSettingsLoaded(),
      auth.restoreUserIfNeeded(),
    ])
  })
}
