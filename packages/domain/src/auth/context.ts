import type { AuthUserRole } from './types'
import { browserSessionDriver } from './drivers/browser-session-driver'
import type { AuthSessionDriver } from './types'

export interface AuthStoreContextOptions {
  performDeveloperLogin?: (role: AuthUserRole) => Promise<void>
  sessionDriver?: AuthSessionDriver
}

const authStoreContext: AuthStoreContextOptions = {}

export function 配置认证存储上下文(options: AuthStoreContextOptions): void {
  authStoreContext.performDeveloperLogin = options.performDeveloperLogin
  authStoreContext.sessionDriver = options.sessionDriver
}

export function 获取已配置的开发者登录处理器(): AuthStoreContextOptions['performDeveloperLogin'] {
  return authStoreContext.performDeveloperLogin
}

export function 获取已配置的认证会话驱动(): AuthSessionDriver {
  return authStoreContext.sessionDriver ?? browserSessionDriver
}
