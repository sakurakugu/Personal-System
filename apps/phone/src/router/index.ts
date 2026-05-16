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
      path: '/moments',
      name: 'Moments',
      component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/articles',
      name: 'Articles',
      component: () => import('@personal-system/module-articles').then((module) => module.ArticlesPage),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/articles/edit/:id?',
      name: 'ArticleEditor',
      component: () => import('@personal-system/module-articles').then((module) => module.ArticleEditorPage),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/collections',
      name: 'Collections',
      component: () => import('@personal-system/module-collections').then((module) => module.CollectionsPage),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/bills',
      name: 'Bills',
      component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/device-sessions',
      name: 'DeviceSessions',
      component: () => import('@personal-system/module-auth').then((module) => module.DeviceSessionsPage),
      meta: { requiresAuth: true, hideTabBar: true },
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
    {
      path: '/me/account-info',
      name: 'ProfileAccountInfo',
      component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
      props: {
        sessionEndRedirect: { path: '/' },
      },
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
