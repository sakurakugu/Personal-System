import { 创建认证模块 } from '@personal-system/module-auth'
import type { AppModule } from '@personal-system/app-core'

export const desktopModules: AppModule[] = [
  创建认证模块({
    loginPath: '/login',
    loginRouteName: 'DesktopLogin',
    loginComponent: () => import('@/modules/认证/pages/登录页面.vue'),
  }),
]
