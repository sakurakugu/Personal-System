import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'

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
        },
        {
          path: 'device-sessions',
          name: 'DesktopDeviceSessions',
          component: () => import('@/modules/auth/pages/DeviceSessionsPage.vue'),
        },
        {
          path: 'profile',
          name: 'DesktopProfile',
          component: () => import('@/modules/profile/pages/ProfilePage.vue'),
        },
      ],
    },
    {
      path: '/login',
      name: 'DesktopLogin',
      component: () => import('@/modules/auth/pages/LoginPage.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth || to.meta.guestOnly) {
    await auth.restoreUserIfNeeded()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return {
      name: 'DesktopLogin',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'DesktopHome' }
  }
})

export default router
