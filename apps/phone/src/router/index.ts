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
      meta: { requiresAuth: false, tabBarId: 'home', blogView: 'feed' },
    },
    {
      path: '/archive',
      name: 'PhoneBlogArchive',
      component: () => import('@/modules/首页/pages/首页页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true, blogView: 'archive' },
    },
    {
      path: '/announcements',
      name: 'PhoneBlogAnnouncements',
      component: () => import('@/modules/首页/pages/首页页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true, blogView: 'announcements' },
    },
    {
      path: '/blog/:slug',
      name: 'PhoneBlogArticleDetail',
      component: () => import('@/modules/首页/pages/首页页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true, blogView: 'feed' },
    },
    {
      path: '/moments/:momentId',
      name: 'PhoneBlogMomentDetail',
      component: () => import('@/modules/首页/pages/首页页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true, blogView: 'feed' },
    },
    {
      path: '/todos',
      name: 'Todos',
      component: () => import('@/modules/待办/pages/待办页面.vue'),
      meta: { requiresAuth: true, tabBarId: 'todos' },
    },
    {
      path: '/memos',
      name: 'Memos',
      component: () => import('@/modules/备忘录/pages/备忘录页面.vue'),
      meta: { requiresAuth: true, tabBarId: 'memos' },
    },
    {
      path: '/moments',
      name: 'Moments',
      component: () => import('@/modules/动态/pages/动态页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true, tabBarId: 'moments' },
    },
    {
      path: '/articles',
      name: 'Articles',
      component: () => import('@/modules/文章/pages/文章页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true, tabBarId: 'articles' },
    },
    {
      path: '/articles/edit/:id?',
      name: 'ArticleEditor',
      component: () => import('@/modules/文章/pages/文章编辑页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/collections',
      name: 'Collections',
      component: () => import('@/modules/收藏/pages/收藏页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true, tabBarId: 'collections' },
    },
    {
      path: '/bills',
      name: 'Bills',
      component: () => import('@/modules/账单/pages/账单页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true, tabBarId: 'bills' },
    },
    {
      path: '/device-sessions',
      name: 'DeviceSessions',
      component: () => import('@/modules/认证/pages/登录设备页面.vue'),
      meta: { requiresAuth: true, hideTabBar: true },
    },
    {
      path: '/me',
      name: 'Profile',
      component: () => import('@/modules/个人/pages/个人页面.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/me/theme',
      name: 'ProfileTheme',
      component: () => import('@/modules/个人/pages/主题页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true },
    },
    {
      path: '/me/settings',
      name: 'ProfileSettings',
      component: () => import('@/modules/个人/pages/设置页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true },
    },
    {
      path: '/me/phone-usage',
      name: 'PhoneUsage',
      component: () => import('@/modules/手机使用/pages/手机使用页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true },
    },
    {
      path: '/me/tab-bar',
      name: 'ProfileTabBar',
      component: () => import('@/modules/个人/pages/标签栏页面.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/me/api-environment',
      name: 'ProfileApiEnvironment',
      component: () => import('@/modules/个人/pages/接口环境页面.vue'),
      meta: { requiresAuth: false, hideTabBar: true },
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
