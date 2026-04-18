import type { RouteRecordRaw } from 'vue-router'

export const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../../views/dashboard/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'DashboardHome',
        component: () => import('../../views/dashboard/DashboardHome.vue'),
      },
      {
        path: 'profile',
        name: 'DashboardProfile',
        component: () => import('../../views/dashboard/ProfilePage.vue'),
      },
      {
        path: 'user-settings',
        name: 'DashboardUserSettings',
        component: () => import('../../views/dashboard/UserSettingsPage.vue'),
      },
      {
        path: 'todos',
        name: 'DashboardTodos',
        component: () => import('../../modules/todos/dashboard/pages/TodosPage.vue'),
      },
      {
        path: 'bills',
        name: 'DashboardBills',
        component: () => import('../../views/dashboard/BillsPage.vue'),
      },
      {
        path: 'moments',
        name: 'DashboardMoments',
        component: () => import('../../views/dashboard/MomentsManage.vue'),
      },
      {
        path: 'collections',
        name: 'DashboardCollections',
        component: () => import('../../modules/collections/dashboard/pages/CollectionsPage.vue'),
      },
      {
        path: 'articles',
        name: 'DashboardArticles',
        component: () => import('../../views/dashboard/ArticlesManage.vue'),
      },
      {
        path: 'articles/edit/:id?',
        name: 'ArticleEditor',
        component: () => import('../../views/dashboard/ArticleEditor.vue'),
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
        component: () => import('../../views/dashboard/SystemPage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'users',
        name: 'UsersManage',
        component: () => import('../../views/dashboard/UsersManage.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'settings',
        name: 'DashboardSettings',
        component: () => import('../../views/dashboard/SettingsPage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'announcements',
        name: 'AnnouncementsManage',
        component: () => import('../../views/dashboard/AnnouncementsManage.vue'),
        meta: { requiresSuperAdmin: true },
      },
      {
        path: 'comments',
        name: 'CommentsManage',
        component: () => import('../../views/dashboard/CommentsManage.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'friend-links',
        name: 'FriendLinksManage',
        component: () => import('../../modules/friend-links/dashboard/pages/FriendLinksManage.vue'),
        meta: { requiresSuperAdmin: true },
      },
    ],
  },
]
