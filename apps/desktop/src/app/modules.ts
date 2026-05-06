import { createAuthModule } from '@personal-system/modules/auth'
import type { AppModule } from '@personal-system/app-core'

export const desktopModules: AppModule[] = [
  createAuthModule({
    loginPath: '/login',
    loginRouteName: 'DesktopLogin',
    loginComponent: () => import('@/modules/auth/pages/LoginPage.vue'),
  }),
]
