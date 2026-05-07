import { collectModuleRoutes, registerStandardAuthGuard } from '@personal-system/app-core'
import { useAuthStore } from '@personal-system/domain/auth'
import { createRouter, createWebHistory } from 'vue-router'
import { desktopNavItems } from '../app/navigation'
import { desktopModules } from '../app/modules'

const [homeNavItem, deviceSessionsNavItem, profileNavItem] = desktopNavItems

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/app/layouts/DesktopLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'DesktopHome',
          component: () => import('@/modules/home/pages/HomePage.vue'),
          meta: { title: homeNavItem.label },
        },
        {
          path: 'device-sessions',
          name: 'DesktopDeviceSessions',
          component: () => import('@/modules/auth/pages/DeviceSessionsPage.vue'),
          meta: { title: deviceSessionsNavItem.label },
        },
        {
          path: 'profile',
          name: 'DesktopProfile',
          component: () => import('@/modules/profile/pages/ProfilePage.vue'),
          meta: { title: profileNavItem.label },
        },
      ],
    },
    ...collectModuleRoutes(desktopModules),
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

registerStandardAuthGuard(router, () => useAuthStore(), {
  loginRouteName: 'DesktopLogin',
  authenticatedRouteName: 'DesktopHome',
})

export default router
