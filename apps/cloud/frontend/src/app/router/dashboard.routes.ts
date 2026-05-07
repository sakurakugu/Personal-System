import type { RouteRecordRaw } from 'vue-router'

export const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true, consoleView: true },
    children: [
      {
        path: '',
        name: 'DashboardHome',
        component: () => import('../../modules/system/dashboard/pages/DashboardHome.vue'),
      },
      {
        path: 'profile',
        name: 'DashboardProfile',
        component: () => import('../../modules/auth/dashboard/pages/ProfilePage.vue'),
      },
      {
        path: 'user-settings',
        name: 'DashboardUserSettings',
        component: () => import('../../modules/auth/dashboard/pages/UserSettingsPage.vue'),
      },
      {
        path: 'device-sessions',
        name: 'DashboardDeviceSessions',
        component: () => import('../../modules/auth/dashboard/pages/DeviceSessionsPage.vue'),
      },
      {
        path: 'todos',
        name: 'DashboardTodos',
        component: () => import('@personal-system/modules/todos').then((module) => module.TodosPage),
      },
      {
        path: 'bills',
        name: 'DashboardBills',
        component: () => import('../../modules/bills/dashboard/pages/BillsPage.vue'),
      },
      {
        path: 'moments',
        name: 'DashboardMoments',
        component: () => import('../../modules/moments/dashboard/pages/MomentsManage.vue'),
      },
      {
        path: 'collections',
        name: 'DashboardCollections',
        component: () => import('../../modules/collections/dashboard/pages/CollectionsPage.vue'),
      },
      {
        path: 'articles',
        name: 'DashboardArticles',
        component: () => import('../../modules/articles/dashboard/pages/ArticlesManage.vue'),
      },
      {
        path: 'articles/edit/:id?',
        name: 'ArticleEditor',
        component: () => import('../../modules/articles/dashboard/pages/ArticleEditor.vue'),
      },
      {
        path: 'files',
        name: 'DashboardFiles',
        component: () => import('../../modules/files/dashboard/pages/FilesPage.vue'),
      },
      {
        path: 'stats',
        name: 'DashboardStats',
        component: () => import('../../modules/system/dashboard/pages/StatsPage.vue'),
      },
      {
        path: 'system',
        name: 'SystemStatus',
        component: () => import('../../modules/admin/dashboard/pages/SystemPage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'users',
        name: 'UsersManage',
        component: () => import('../../modules/admin/dashboard/pages/UsersManage.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'settings',
        name: 'DashboardSettings',
        component: () => import('../../modules/admin/dashboard/pages/SettingsPage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'announcements',
        name: 'AnnouncementsManage',
        component: () => import('../../modules/admin/dashboard/pages/AnnouncementsManage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'friend-links',
        name: 'FriendLinksManage',
        component: () => import('../../modules/friend-links/dashboard/pages/FriendLinksManage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'twikoo',
        name: 'TwikooManage',
        component: () => import('../../modules/admin/dashboard/pages/TwikooManage.vue'),
        meta: { requiresSuperAdmin: true },
      },
    ],
  },
]
