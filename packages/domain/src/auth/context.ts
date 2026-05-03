import type { AuthUserRole } from './types'
import { browserSessionDriver } from './drivers/browser-session-driver'
import type { AuthSessionDriver } from './types'

export interface AuthStoreContextOptions {
  performDeveloperLogin?: (role: AuthUserRole) => Promise<void>
  sessionDriver?: AuthSessionDriver
}

const authStoreContext: AuthStoreContextOptions = {}

export function configureAuthStoreContext(options: AuthStoreContextOptions): void {
  authStoreContext.performDeveloperLogin = options.performDeveloperLogin
  authStoreContext.sessionDriver = options.sessionDriver
}

export function getConfiguredDeveloperLoginHandler(): AuthStoreContextOptions['performDeveloperLogin'] {
  return authStoreContext.performDeveloperLogin
}

export function getConfiguredAuthSessionDriver(): AuthSessionDriver {
  return authStoreContext.sessionDriver ?? browserSessionDriver
}
