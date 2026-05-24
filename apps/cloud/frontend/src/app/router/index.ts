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
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }

    if (to.hash) {
      return {
        el: to.hash,
        top: 80,
        behavior: 'smooth',
      }
    }

    // 仅在真正切换页面时回到顶部，避免仅修改查询参数时打断当前浏览位置。
    if (to.path !== from.path) {
      return {
        left: 0,
        top: 0,
        behavior: 'auto',
      }
    }

    return undefined
  },
})

注册路由守卫(router)

export default router
