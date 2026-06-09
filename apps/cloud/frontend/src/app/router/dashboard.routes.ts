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
        meta: { searchPlaceholder: '搜索待办', searchTarget: 'current' },
      },
      {
        path: 'bills',
        name: 'DashboardBills',
        component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
        meta: { searchPlaceholder: '搜索账单', searchTarget: 'current' },
      },
      {
        path: 'moments',
        name: 'DashboardMoments',
        component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
      },
      {
        path: 'memos',
        name: 'DashboardMemos',
        component: () => import('@personal-system/module-memos').then((module) => module.MemosPage),
        meta: { searchPlaceholder: '搜索备忘录', searchTarget: 'current' },
      },
      {
        path: 'materials',
        name: 'DashboardCollections',
        component: () => import('@personal-system/module-materials').then((module) => module.MaterialsPage),
        meta: { searchPlaceholder: '搜索资料', searchTarget: 'current' },
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
        meta: { searchPlaceholder: '搜索文件', searchTarget: 'current' },
      },
      {
        path: 'media',
        name: 'DashboardMedia',
        component: () => import('@personal-system/module-media').then((module) => module.MediaPage),
        meta: { searchPlaceholder: '搜索文娱作品', searchTarget: 'current' },
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
