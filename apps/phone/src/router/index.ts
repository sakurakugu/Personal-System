import { collectModuleRoutes, registerStandardAuthGuard } from '@personal-system/app-core'
import { useAuthStore, useLoginGateStore } from '@personal-system/domain/auth'
import { createRouter, createWebHistory } from 'vue-router'
import { phoneModules } from '../app/modules'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...collectModuleRoutes(phoneModules),
    {
      path: '/',
      name: 'Home',
      component: () => import('@/modules/home/pages/HomePage.vue'),
      meta: { requiresAuth: false },
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
    {
      path: '/me/account',
      name: 'ProfileAccount',
      component: () => import('@/modules/profile/pages/ProfileAccountPage.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/account/details',
      name: 'ProfileAccountDetails',
      component: () => import('@/modules/profile/pages/ProfileAccountDetailsPage.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/account/role',
      name: 'ProfileRole',
      component: () => import('@/modules/profile/pages/ProfileRolePage.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/theme',
      name: 'ProfileTheme',
      component: () => import('@/modules/profile/pages/ProfileThemePage.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/tab-bar',
      name: 'ProfileTabBar',
      component: () => import('@/modules/profile/pages/ProfileTabBarPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/me/api-environment',
      name: 'ProfileApiEnvironment',
      component: () => import('@/modules/profile/pages/ProfileApiEnvironmentPage.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
  ],
})

registerStandardAuthGuard(router, () => useAuthStore(), {
  loginRouteName: 'Login',
  authenticatedRouteName: 'Home',
  handleUnauthorizedRoute: (to) => {
    useLoginGateStore().open({ redirectPath: to.fullPath })
  },
})

export default router
