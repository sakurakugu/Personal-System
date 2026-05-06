import { resolveStandardAuthGuardRedirect } from '@personal-system/app-core'
import type { Router } from 'vue-router'
import { useAuthStore } from '../../modules/auth/store'
import { useSettingsStore } from '../../shared/stores/settings'

export function registerRouteGuards(router: Router): void {
  router.beforeEach(async (to) => {
    const auth = useAuthStore()
    const settings = useSettingsStore()
    if (to.name === 'BlogGuestbook') {
      await settings.ensurePublicSettingsLoaded()
      if (settings.commentsHidden) {
        return { name: 'BlogAbout' }
      }
    }
    return resolveStandardAuthGuardRedirect(to, auth, {
      loginRouteName: 'BlogHome',
      authenticatedRouteName: 'DashboardHome',
      unauthorizedRouteName: 'DashboardHome',
      loginQueryFactory: () => ({ login: '1' }),
    })
  })
}
