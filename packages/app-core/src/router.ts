import type { RouteLocationNormalizedGeneric, RouteRecordNameGeneric, Router } from 'vue-router'

export interface AuthGuardStoreLike {
  isAdmin?: boolean
  isAuthenticated: boolean
  isSuperAdmin?: boolean
  restoreUserIfNeeded?: () => Promise<void>
  需要时恢复用户: () => Promise<void>
}

export interface StandardAuthGuardOptions {
  authenticatedRouteName: RouteRecordNameGeneric
  handleUnauthorizedRoute?: (to: RouteLocationNormalizedGeneric) => void | Promise<void>
  loginQueryFactory?: (to: RouteLocationNormalizedGeneric) => Record<string, string>
  loginRouteName: RouteRecordNameGeneric
  unauthorizedRouteName?: RouteRecordNameGeneric
}

export async function 解析标准认证守卫重定向(
  to: RouteLocationNormalizedGeneric,
  authStore: AuthGuardStoreLike,
  options: StandardAuthGuardOptions,
) {
  const requiresProtectedUser = Boolean(
    to.meta.requiresAuth
    || to.meta.requiresAdmin
    || to.meta.requiresSuperAdmin
    || to.meta.guestOnly,
  )

  if (requiresProtectedUser) {
    await authStore.需要时恢复用户()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    if (options.handleUnauthorizedRoute) {
      await options.handleUnauthorizedRoute(to)
      return false
    }

    return {
      name: options.loginRouteName,
      query: options.loginQueryFactory?.(to) ?? { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: options.unauthorizedRouteName ?? options.authenticatedRouteName }
  }

  if (to.meta.requiresSuperAdmin && !authStore.isSuperAdmin) {
    return { name: options.unauthorizedRouteName ?? options.authenticatedRouteName }
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: options.authenticatedRouteName }
  }

  return undefined
}

export function 注册标准认证守卫(
  router: Router,
  getAuthStore: () => AuthGuardStoreLike,
  options: StandardAuthGuardOptions,
): void {
  router.beforeEach(async (to) => {
    return 解析标准认证守卫重定向(to, getAuthStore(), options)
  })
}
