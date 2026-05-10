import { collectModuleRoutes, registerStandardAuthGuard } from '@personal-system/app-core'
import { useAuthStore, useLoginGateStore } from '@personal-system/domain/auth'
import { createRouter, createWebHistory } from 'vue-router'
import { getDesktopRouteTitle } from '../app/navigation'
import { desktopModules } from '../app/modules'
import { useDesktopTabsStore } from '../shared/stores/tabs'

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
          meta: { requiresAuth: false, title: getDesktopRouteTitle('/') },
        },
        {
          path: 'todos',
          name: 'DesktopTodos',
          component: () => import('@personal-system/module-todos').then((module) => module.TodosPage),
          meta: { title: getDesktopRouteTitle('/todos') },
        },
        {
          path: 'collections',
          name: 'DesktopCollections',
          component: () => import('@personal-system/module-collections').then((module) => module.CollectionsPage),
          meta: { title: getDesktopRouteTitle('/collections') },
        },
        {
          path: 'articles',
          name: 'DesktopArticles',
          component: () => import('@personal-system/module-articles').then((module) => module.ArticlesPage),
          meta: { title: getDesktopRouteTitle('/articles') },
        },
        {
          path: 'articles/edit/:id?',
          name: 'DesktopArticleEditor',
          component: () => import('@personal-system/module-articles').then((module) => module.ArticleEditorPage),
          meta: { title: getDesktopRouteTitle('/articles'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'files',
          name: 'DesktopFiles',
          component: () => import('@personal-system/module-files').then((module) => module.FilesPage),
          meta: { title: getDesktopRouteTitle('/files'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'bills',
          name: 'DesktopBills',
          component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
          meta: { title: getDesktopRouteTitle('/bills') },
        },
        {
          path: 'moments',
          name: 'DesktopMoments',
          component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
          meta: { title: getDesktopRouteTitle('/moments'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools',
          name: 'DesktopTools',
          component: () => import('@personal-system/module-tools').then((module) => module.ToolsPage),
          meta: { requiresAuth: false, title: getDesktopRouteTitle('/tools') },
        },
        {
          path: 'tools/image',
          name: 'DesktopImageTools',
          component: () => import('@personal-system/module-tools').then((module) => module.ImageToolsPage),
          meta: { requiresAuth: false, title: getDesktopRouteTitle('/tools/image'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools/image-classifier',
          name: 'DesktopImageClassifier',
          component: () => import('@/modules/tools/pages/ImageClassifierPage.vue'),
          meta: { requiresAuth: false, title: getDesktopRouteTitle('/tools/image-classifier'), keepAlive: true },
        },
        {
          path: 'tools/minecraft-server',
          name: 'DesktopMinecraftServerQuery',
          component: () => import('@/modules/tools/pages/MinecraftServerQueryPage.vue'),
          meta: { requiresAuth: false, title: getDesktopRouteTitle('/tools/minecraft-server'), keepAlive: true, preserveTabOnNavigate: true },
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
          component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
          props: {
            sessionEndRedirect: { path: '/' },
            onSessionEnded: () => useDesktopTabsStore().reset('/'),
          },
          meta: { title: getDesktopRouteTitle('/profile') },
        },
        {
          path: 'settings',
          name: 'DesktopSettings',
          component: () => import('@/modules/settings/pages/SettingsPage.vue'),
          meta: { title: getDesktopRouteTitle('/settings') },
        },
        {
          path: 'settings/api-environment',
          name: 'DesktopSettingsApiEnvironment',
          component: () => import('@/modules/settings/pages/SettingsApiEnvironmentPage.vue'),
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
