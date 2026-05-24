import { 收集模块路由, 注册标准认证守卫 } from '@personal-system/app-core'
import { 使用认证存储, 使用登录门禁存储 } from '@personal-system/domain/auth'
import { createRouter, createWebHistory } from 'vue-router'
import { phoneModules } from '../app/modules'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...收集模块路由(phoneModules),
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
      path: '/me/theme',
      name: 'ProfileTheme',
      component: () => import('@/modules/个人/pages/主题页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me/settings',
      name: 'ProfileSettings',
      component: () => import('@/modules/个人/pages/设置页面.vue'),
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
      path: '/me/account',
      name: 'ProfileAccount',
      component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
      props: {
        sessionEndRedirect: { path: '/' },
      },
      meta: { requiresAuth: true, hideTabBar: true },
    },
  ],
})

注册标准认证守卫(router, () => 使用认证存储(), {
  loginRouteName: 'Login',
  authenticatedRouteName: 'Home',
  handleUnauthorizedRoute: (to) => {
    使用登录门禁存储().open({ redirectPath: to.fullPath })
  },
})

export default router
