import { createAuthModule } from '@personal-system/module-auth'
import type { AppModule } from '@personal-system/app-core'

export const desktopModules: AppModule[] = [
  createAuthModule({
    loginPath: '/login',
    loginRouteName: 'DesktopLogin',
    loginComponent: () => import('@/modules/认证/pages/登录页面.vue'),
  }),
]
