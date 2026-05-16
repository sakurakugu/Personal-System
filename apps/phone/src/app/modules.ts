import { 创建认证模块 } from '@personal-system/module-auth'
import type { AppModule } from '@personal-system/app-core'

export const phoneModules: AppModule[] = [
  创建认证模块({
    loginPath: '/login',
    loginRouteName: 'Login',
    loginComponent: () => import('@/modules/认证/pages/登录页面.vue'),
    loginRouteMeta: { hideTabBar: true },
  }),
]
