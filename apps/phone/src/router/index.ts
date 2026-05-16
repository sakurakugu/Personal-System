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
      component: () => import('@/modules/首页/pages/首页页面.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/todos',
      name: 'Todos',
      component: () => import('@/modules/待办/pages/待办页面.vue'),
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
      component: () => import('@/modules/个人/pages/个人页面.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/me/account',
      name: 'ProfileAccount',
      component: () => import('@/modules/个人/pages/账户页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/account/details',
      name: 'ProfileAccountDetails',
      component: () => import('@/modules/个人/pages/账户详情页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/account/role',
      name: 'ProfileRole',
      component: () => import('@/modules/个人/pages/角色页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/theme',
      name: 'ProfileTheme',
      component: () => import('@/modules/个人/pages/主题页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/tab-bar',
      name: 'ProfileTabBar',
      component: () => import('@/modules/个人/pages/标签栏页面.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/me/api-environment',
      name: 'ProfileApiEnvironment',
      component: () => import('@/modules/个人/pages/接口环境页面.vue'),
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
