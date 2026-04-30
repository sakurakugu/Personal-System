import type { Router } from 'vue-router'
import { useAuthStore } from '../../modules/auth/store'
import { useSettingsStore } from '../../shared/stores/settings'

export function registerRouteGuards(router: Router): void {
  router.beforeEach(async (to) => {
    const auth = useAuthStore()
    const settings = useSettingsStore()
    const requiresProtectedUser = Boolean(
      to.meta.requiresAuth
      || to.meta.requiresAdmin
      || to.meta.requiresSuperAdmin,
    )

    if (requiresProtectedUser) {
      await auth.restoreUserIfNeeded()
    }
    if (to.name === 'BlogGuestbook') {
      await settings.ensurePublicSettingsLoaded()
      if (settings.commentsHidden) {
        return { name: 'BlogAbout' }
      }
    }

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
      return { name: 'BlogHome', query: { login: '1' } }
    }
    if (to.meta.requiresAdmin && !auth.isAdmin) {
      return { name: 'DashboardHome' }
    }
    if (to.meta.requiresSuperAdmin && !auth.isSuperAdmin) {
      return { name: 'DashboardHome' }
    }
  })
}
