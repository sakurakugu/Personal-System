import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { blogRoutes } from './blog.routes'
import { dashboardRoutes } from './dashboard.routes'
import { registerRouteGuards } from './guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/blog',
  },
  ...blogRoutes,
  ...dashboardRoutes,
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../pages/NotFoundPage.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

registerRouteGuards(router)

export default router
