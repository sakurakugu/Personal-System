import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { blogRoutes } from './blog.routes'
import { dashboardRoutes } from './dashboard.routes'
import { toolsRoutes } from './tools.routes'
import { 注册路由守卫 } from './guards'

const 博客首页视图路由名称 = new Set([
  'BlogHome',
  'BlogArchive',
  'BlogAnnouncements',
  'BlogFriends',
  'BlogAbout',
  'BlogGuestbook',
  'BlogSponsor',
  'BlogBangumi',
  'BlogGallery',
  'BlogRss',
])

function 是否为博客首页壳内切换(routeName: unknown) {
  return typeof routeName === 'string' && 博客首页视图路由名称.has(routeName)
}

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

    // 博客首页的多个栏目共用同一页壳，切换时保留当前滚动位置，避免体验突兀。
    if (是否为博客首页壳内切换(to.name) && 是否为博客首页壳内切换(from.name)) {
      if (import.meta.env.DEV) {
        console.debug('[router] 保留博客首页壳内切换滚动位置', {
          from: from.fullPath,
          to: to.fullPath,
        })
      }
      return false
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
