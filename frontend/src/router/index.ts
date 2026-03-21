import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/blog',
    },
    {
      path: '/blog',
      name: 'BlogHome',
      component: () => import('../views/blog/BlogHome.vue'),
    },
    {
      path: '/blog/:slug',
      name: 'ArticleDetail',
      component: () => import('../views/blog/ArticleDetail.vue'),
    },
    {
      path: '/search',
      name: 'SearchPage',
      component: () => import('../views/blog/SearchPage.vue'),
    },
    {
      path: '/announcements',
      name: 'AnnouncementsPage',
      component: () => import('../views/blog/AnnouncementsPage.vue'),
    },
    {
      path: '/links',
      name: 'LinksPage',
      component: () => import('../views/blog/LinksPage.vue'),
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/dashboard/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'DashboardHome',
          component: () => import('../views/dashboard/DashboardHome.vue'),
        },
        {
          path: 'profile',
          name: 'DashboardProfile',
          component: () => import('../views/dashboard/ProfilePage.vue'),
        },
        {
          path: 'todos',
          name: 'DashboardTodos',
          component: () => import('../views/dashboard/TodosPage.vue'),
        },
        {
          path: 'articles',
          name: 'DashboardArticles',
          component: () => import('../views/dashboard/ArticlesManage.vue'),
        },
        {
          path: 'articles/edit/:id?',
          name: 'ArticleEditor',
          component: () => import('../views/dashboard/ArticleEditor.vue'),
        },
        {
          path: 'files',
          name: 'DashboardFiles',
          component: () => import('../views/dashboard/FilesPage.vue'),
        },
        {
          path: 'stats',
          name: 'DashboardStats',
          component: () => import('../views/dashboard/StatsPage.vue'),
        },
        {
          path: 'system',
          name: 'SystemStatus',
          component: () => import('../views/dashboard/SystemPage.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'users',
          name: 'UsersManage',
          component: () => import('../views/dashboard/UsersManage.vue'),
          meta: { requiresSuperAdmin: true },
        },
        {
          path: 'settings',
          name: 'DashboardSettings',
          component: () => import('../views/dashboard/SettingsPage.vue'),
          meta: { requiresSuperAdmin: true },
        },
        {
          path: 'announcements',
          name: 'AnnouncementsManage',
          component: () => import('../views/dashboard/AnnouncementsManage.vue'),
          meta: { requiresSuperAdmin: true },
        },
        {
          path: 'links',
          name: 'LinksManage',
          component: () => import('../views/dashboard/LinksManage.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('../views/NotFoundPage.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Try to restore session on first load
  if (auth.accessToken && !auth.user) {
    await auth.fetchUser()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'BlogHome', query: { login: '1' } }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'DashboardHome' }
  }
  if (to.meta.requiresSuperAdmin && !auth.isSuperAdmin) {
    return { name: 'DashboardHome' }
  }
})

export default router
