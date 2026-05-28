import type { RouteRecordRaw } from 'vue-router'

export const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../layouts/控制台布局.vue'),
    meta: { requiresAuth: true, consoleView: true },
    redirect: '/dashboard/stats',
    children: [
      {
        path: 'profile',
        name: 'DashboardProfile',
        component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
        props: {
          sessionEndRedirect: { name: 'BlogHome', query: { login: '1' } },
        },
      },
      {
        path: 'user-settings',
        name: 'DashboardUserSettings',
        component: () => import('../../modules/认证/dashboard/pages/用户设置页面.vue'),
      },
      {
        path: 'device-sessions',
        name: 'DashboardDeviceSessions',
        component: () => import('@personal-system/module-auth').then((module) => module.DeviceSessionsPage),
      },
      {
        path: 'todos',
        name: 'DashboardTodos',
        component: () => import('@personal-system/module-todos').then((module) => module.TodosPage),
      },
      {
        path: 'bills',
        name: 'DashboardBills',
        component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
      },
      {
        path: 'moments',
        name: 'DashboardMoments',
        component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
      },
      {
        path: 'collections',
        name: 'DashboardCollections',
        component: () => import('@personal-system/module-collections').then((module) => module.CollectionsPage),
      },
      {
        path: 'articles',
        name: 'DashboardArticles',
        component: () => import('@personal-system/module-articles').then((module) => module.ArticlesPage),
      },
      {
        path: 'articles/edit/:id?',
        name: 'ArticleEditor',
        component: () => import('@personal-system/module-articles').then((module) => module.ArticleEditorPage),
      },
      {
        path: 'files',
        name: 'DashboardFiles',
        component: () => import('@personal-system/module-files').then((module) => module.FilesPage),
      },
      {
        path: 'media',
        name: 'DashboardMedia',
        component: () => import('@personal-system/module-media').then((module) => module.MediaPage),
      },
      {
        path: 'stats',
        name: 'DashboardStats',
        component: () => import('../../modules/系统/dashboard/pages/统计页面.vue'),
      },
      {
        path: 'system',
        name: 'SystemStatus',
        component: () => import('../../modules/管理/dashboard/pages/系统页面.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'users',
        name: 'UsersManage',
        component: () => import('../../modules/管理/dashboard/pages/用户管理页面.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'settings',
        name: 'DashboardSettings',
        component: () => import('../../modules/管理/dashboard/pages/设置页面.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'announcements',
        name: 'AnnouncementsManage',
        component: () => import('../../modules/管理/dashboard/pages/公告管理页面.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'friend-links',
        name: 'FriendLinksManage',
        component: () => import('../../modules/友链/dashboard/pages/友链管理页面.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'ai',
        name: 'AIManage',
        component: () => import('../../modules/管理/dashboard/pages/AI管理页面.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'twikoo',
        name: 'TwikooManage',
        component: () => import('../../modules/管理/dashboard/pages/评论管理页面.vue'),
        meta: { requiresSuperAdmin: true },
      },
    ],
  },
]
