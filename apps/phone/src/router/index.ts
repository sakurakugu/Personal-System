import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@personal-system/domain/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/modules/auth/pages/LoginPage.vue'),
      meta: { hideTabBar: true, guestOnly: true },
    },
    {
      path: '/',
      name: 'Home',
      component: () => import('@/modules/home/pages/HomePage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/todos',
      name: 'Todos',
      component: () => import('@/modules/todos/pages/TodosPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/me',
      name: 'Profile',
      component: () => import('@/modules/profile/pages/ProfilePage.vue'),
      meta: { requiresAuth: true },
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
      name: 'Login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'Home' }
  }
})

export default router
