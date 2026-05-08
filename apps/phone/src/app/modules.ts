import { createAuthModule } from '@personal-system/module-auth'
import type { AppModule } from '@personal-system/app-core'

export const phoneModules: AppModule[] = [
  createAuthModule({
    loginPath: '/login',
    loginRouteName: 'Login',
    loginComponent: () => import('@/modules/auth/pages/LoginPage.vue'),
    loginRouteMeta: { hideTabBar: true },
  }),
]
