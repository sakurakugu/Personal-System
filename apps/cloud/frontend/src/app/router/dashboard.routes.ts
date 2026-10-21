import type { RouteRecordRaw } from 'vue-router'

// 各后台页面统一补充 meta.title，控制台多标签页直接使用该标题（文案与左侧菜单保持一致）。
export const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../layouts/控制台布局.vue'),
    meta: { requiresAuth: true, consoleView: true },
    redirect: '/dashboard/stats/blog',
    children: [
      {
        path: 'blog',
        name: 'DashboardBlogManage',
        component: () => import('@personal-system/module-blog').then((module) => module.BlogManagePage),
        meta: { title: '博客管理' },
      },
      {
        path: 'profile',
        name: 'DashboardProfile',
        component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
        meta: { title: '个人资料' },
        props: {
          sessionEndRedirect: { name: 'BlogHome', query: { login: '1' } },
        },
      },
      {
        path: 'device-sessions',
        name: 'DashboardDeviceSessions',
        component: () => import('@personal-system/module-auth').then((module) => module.DeviceSessionsPage),
        meta: { title: '登录设备' },
      },
      {
        path: 'todos',
        name: 'DashboardTodos',
        component: () => import('@personal-system/module-todos').then((module) => module.TodosPage),
        meta: { title: '待办事项', searchPlaceholder: '搜索待办', searchTarget: 'current' },
      },
      {
        path: 'bills',
        name: 'DashboardBills',
        component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
        meta: { title: '账单管理', searchPlaceholder: '搜索账单', searchTarget: 'current' },
      },
      {
        path: 'moments',
        name: 'DashboardMoments',
        component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
        meta: { title: '动态管理' },
      },
      {
        path: 'materials',
        name: 'DashboardCollections',
        component: () => import('@personal-system/module-materials').then((module) => module.MaterialsPage),
        meta: { title: '资料库', searchPlaceholder: '搜索资料', searchTarget: 'current' },
      },
      {
        path: 'articles',
        name: 'DashboardArticles',
        component: () => import('@personal-system/module-articles').then((module) => module.ArticlesPage),
        meta: { title: '文章管理' },
      },
      {
        path: 'articles/edit/:id?',
        name: 'ArticleEditor',
        component: () => import('@personal-system/module-articles').then((module) => module.ArticleEditorPage),
        meta: { title: '文章编辑' },
      },
      {
        path: 'files',
        name: 'DashboardFiles',
        component: () => import('@personal-system/module-files').then((module) => module.FilesPage),
        meta: { title: '文件管理', searchPlaceholder: '搜索文件', searchTarget: 'current' },
      },
      {
        path: 'media',
        name: 'DashboardMedia',
        component: () => import('@personal-system/module-media').then((module) => module.MediaPage),
        meta: { title: '作品推荐', searchPlaceholder: '搜索文娱作品', searchTarget: 'current' },
      },
      {
        path: 'stats',
        name: 'DashboardStats',
        redirect: '/dashboard/stats/blog',
        meta: { title: '博客统计' },
      },
      {
        path: 'stats/blog',
        name: 'DashboardBlogStats',
        component: () => import('../../modules/系统/dashboard/pages/博客统计页面.vue'),
        meta: { title: '博客统计' },
      },
      {
        path: 'stats/other',
        name: 'DashboardDataStats',
        component: () => import('@personal-system/module-stats').then((module) => module.DataStatsPage),
        meta: { title: '数据统计' },
      },
      {
        path: 'system',
        name: 'SystemStatus',
        component: () => import('../../modules/管理/dashboard/pages/系统页面.vue'),
        meta: { title: '系统状态' },
      },
      {
        path: 'settings',
        name: 'DashboardSettings',
        component: () => import('../../modules/管理/dashboard/pages/设置页面.vue'),
        meta: { title: '系统设置' },
      },
      {
        path: 'announcements',
        name: 'AnnouncementsManage',
        component: () => import('../../modules/管理/dashboard/pages/公告管理页面.vue'),
        meta: { title: '公告管理' },
      },
      {
        path: 'friend-links',
        name: 'FriendLinksManage',
        component: () => import('../../modules/友链/dashboard/pages/友链管理页面.vue'),
        meta: { title: '友链管理' },
      },
      {
        path: 'ai',
        name: 'AIManage',
        component: () => import('../../modules/管理/dashboard/pages/AI管理页面.vue'),
        meta: { title: 'AI 管理' },
      },
      {
        path: 'twikoo',
        name: 'TwikooManage',
        component: () => import('../../modules/管理/dashboard/pages/评论管理页面.vue'),
        meta: { title: '评论管理' },
      },
    ],
  },
]
