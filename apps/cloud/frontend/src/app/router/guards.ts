import { 解析标准认证守卫重定向 } from '@personal-system/app-core'
import { useAuthStore } from '@personal-system/domain/auth'
import type { Router } from 'vue-router'
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
    return 解析标准认证守卫重定向(to, auth, {
      loginRouteName: 'BlogHome',
      authenticatedRouteName: 'DashboardHome',
      unauthorizedRouteName: 'DashboardHome',
      loginQueryFactory: () => ({ login: '1' }),
    })
  })
}
