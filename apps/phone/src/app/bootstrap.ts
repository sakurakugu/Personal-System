import type { Pinia } from 'pinia'
import { configureAuthStoreContext, useAuthStore } from '@personal-system/domain/auth'
import { configureApiClientContext } from '@personal-system/api'

let appBootstrapTask: Promise<void> | null = null

export function initializeAppShell(pinia: Pinia): Promise<void> {
  if (appBootstrapTask) {
    return appBootstrapTask
  }

  appBootstrapTask = (async () => {
    const auth = useAuthStore(pinia)

    configureApiClientContext({
      handleUnauthorized: () => auth.clearSession(),
    })
    configureAuthStoreContext({})

    await auth.restoreUserIfNeeded()
  })()

  return appBootstrapTask
}
