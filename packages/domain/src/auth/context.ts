import type { AuthUserRole } from './types'

export interface AuthStoreContextOptions {
  performDeveloperLogin?: (role: AuthUserRole) => Promise<void>
}

const authStoreContext: AuthStoreContextOptions = {}

export function configureAuthStoreContext(options: AuthStoreContextOptions): void {
  authStoreContext.performDeveloperLogin = options.performDeveloperLogin
}

export function getConfiguredDeveloperLoginHandler(): AuthStoreContextOptions['performDeveloperLogin'] {
  return authStoreContext.performDeveloperLogin
}
