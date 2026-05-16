import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { blogRoutes } from './blog.routes'
import { dashboardRoutes } from './dashboard.routes'
import { toolsRoutes } from './tools.routes'
import { 注册路由守卫 } from './guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/blog',
  },
  ...blogRoutes,
  ...toolsRoutes,
  ...dashboardRoutes,
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../pages/未找到页面.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

注册路由守卫(router)

export default router
