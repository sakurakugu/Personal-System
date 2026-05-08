import { collectModuleRoutes, registerStandardAuthGuard } from '@personal-system/app-core'
import { useAuthStore } from '@personal-system/domain/auth'
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
          meta: { title: getDesktopRouteTitle('/') },
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
          meta: { title: getDesktopRouteTitle('/articles') },
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
          meta: { title: getDesktopRouteTitle('/moments') },
        },
        {
          path: 'tools',
          name: 'DesktopTools',
          component: () => import('@personal-system/module-tools').then((module) => module.ToolsPage),
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
          component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
          props: {
            sessionEndRedirect: { name: 'DesktopLogin' },
            onSessionEnded: () => useDesktopTabsStore().reset('/login'),
          },
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
