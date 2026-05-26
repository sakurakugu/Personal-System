import { 解析标准认证守卫重定向 } from '@personal-system/app-core'
import { 使用认证存储 } from '@personal-system/domain/auth'
import type { Router } from 'vue-router'
import { 使用设置存储 } from '../../shared/stores/settings'

export function 注册路由守卫(router: Router): void {
  router.beforeEach(async (to) => {
    const auth = 使用认证存储()
    const settings = 使用设置存储()
    if (to.name === 'BlogGuestbook') {
      await settings.ensurePublicSettingsLoaded()
      if (settings.commentsHidden) {
        return { name: 'BlogAbout' }
      }
    }
    return 解析标准认证守卫重定向(to, auth, {
      loginRouteName: 'BlogHome',
      authenticatedRouteName: 'DashboardStats',
      unauthorizedRouteName: 'DashboardStats',
      loginQueryFactory: () => ({ login: '1' }),
    })
  })
}
