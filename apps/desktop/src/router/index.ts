import { collectModuleRoutes, registerStandardAuthGuard } from '@personal-system/app-core'
import { useAuthStore, useLoginGateStore } from '@personal-system/domain/auth'
import { createRouter, createWebHistory } from 'vue-router'
import { 获取桌面路由标题 } from '../app/navigation'
import { desktopModules } from '../app/modules'
import { useDesktopTabsStore } from '../shared/stores/tabs'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/app/layouts/桌面布局.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'DesktopHome',
          component: () => import('@/modules/首页/pages/首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/') },
        },
        {
          path: 'todos',
          name: 'DesktopTodos',
          component: () => import('@personal-system/module-todos').then((module) => module.TodosPage),
          meta: { title: 获取桌面路由标题('/todos') },
        },
        {
          path: 'collections',
          name: 'DesktopCollections',
          component: () => import('@personal-system/module-collections').then((module) => module.CollectionsPage),
          meta: { title: 获取桌面路由标题('/collections') },
        },
        {
          path: 'articles',
          name: 'DesktopArticles',
          component: () => import('@personal-system/module-articles').then((module) => module.ArticlesPage),
          meta: { title: 获取桌面路由标题('/articles') },
        },
        {
          path: 'articles/edit/:id?',
          name: 'DesktopArticleEditor',
          component: () => import('@personal-system/module-articles').then((module) => module.ArticleEditorPage),
          meta: { title: 获取桌面路由标题('/articles'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'files',
          name: 'DesktopFiles',
          component: () => import('@personal-system/module-files').then((module) => module.FilesPage),
          meta: { title: 获取桌面路由标题('/files'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'bills',
          name: 'DesktopBills',
          component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
          meta: { title: 获取桌面路由标题('/bills') },
        },
        {
          path: 'moments',
          name: 'DesktopMoments',
          component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
          meta: { title: 获取桌面路由标题('/moments'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools',
          name: 'DesktopTools',
          component: () => import('@/modules/工具/pages/工具首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools') },
        },
        {
          path: 'tools/image',
          name: 'DesktopImageTools',
          component: () => import('@personal-system/module-tools').then((module) => module.ImageToolsPage),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/image'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools/windows',
          name: 'DesktopWindowsTools',
          component: () => import('@/modules/工具/pages/Windows工具页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/windows'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools/image-classifier',
          name: 'DesktopImageClassifier',
          component: () => import('@/modules/工具/pages/图片分类页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/image-classifier'), keepAlive: true },
        },
        {
          path: 'tools/minecraft-server',
          name: 'DesktopMinecraftServerQuery',
          component: () => import('@/modules/工具/pages/MC服务器查询页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/minecraft-server'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'device-sessions',
          name: 'DesktopDeviceSessions',
          component: () => import('@/modules/认证/pages/设备页面.vue'),
          meta: { title: 获取桌面路由标题('/device-sessions') },
        },
        {
          path: 'profile',
          name: 'DesktopProfile',
          component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
          props: {
            sessionEndRedirect: { path: '/' },
            onSessionEnded: () => useDesktopTabsStore().reset('/'),
          },
          meta: { title: 获取桌面路由标题('/profile') },
        },
        {
          path: 'settings',
          name: 'DesktopSettings',
          component: () => import('@/modules/设置/pages/设置页面.vue'),
          meta: { title: 获取桌面路由标题('/settings') },
        },
        {
          path: 'settings/api-environment',
          name: 'DesktopSettingsApiEnvironment',
          component: () => import('@/modules/设置/pages/接口环境页面.vue'),
          meta: { title: '接口环境' },
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
  handleUnauthorizedRoute: (to) => {
    useLoginGateStore().open({ redirectPath: to.fullPath })
  },
})

export default router
