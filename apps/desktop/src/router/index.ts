import { collectModuleRoutes, registerStandardAuthGuard } from '@personal-system/app-core'
import { useAuthStore } from '@personal-system/domain/auth'
import { createRouter, createWebHistory } from 'vue-router'
import { getDesktopRouteTitle } from '../app/navigation'
import { desktopModules } from '../app/modules'

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
          meta: { title: getDesktopRouteTitle('/') },
        },
        {
          path: 'todos',
          name: 'DesktopTodos',
          component: () => import('@/modules/todos/pages/DesktopTodosPage.vue'),
          meta: { title: getDesktopRouteTitle('/todos') },
        },
        {
          path: 'bills',
          name: 'DesktopBills',
          component: () => import('@/modules/bills/pages/DesktopBillsPage.vue'),
          meta: { title: getDesktopRouteTitle('/bills') },
        },
        {
          path: 'moments',
          name: 'DesktopMoments',
          component: () => import('@/modules/moments/pages/DesktopMomentsPage.vue'),
          meta: { title: getDesktopRouteTitle('/moments') },
        },
        {
          path: 'tools',
          name: 'DesktopTools',
          component: () => import('@/modules/tools/pages/ToolsPage.vue'),
          meta: { title: getDesktopRouteTitle('/tools') },
        },
        {
          path: 'device-sessions',
          name: 'DesktopDeviceSessions',
          component: () => import('@/modules/auth/pages/DeviceSessionsPage.vue'),
          meta: { title: getDesktopRouteTitle('/device-sessions') },
        },
        {
          path: 'profile',
          name: 'DesktopProfile',
          component: () => import('@/modules/profile/pages/ProfilePage.vue'),
          meta: { title: getDesktopRouteTitle('/profile') },
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
