import { 收集模块路由, 注册标准认证守卫 } from '@personal-system/app-core'
import { 使用认证存储, 使用登录门禁存储 } from '@personal-system/domain/auth'
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import { 获取桌面路由标题 } from '../app/navigation'
import { desktopModules } from '../app/modules'
import { 使用桌面标签存储 } from '../shared/stores/tabs'

const router = createRouter({
  history: import.meta.env.PROD ? createWebHashHistory() : createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/app/layouts/桌面布局.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/home',
        },
        {
          path: 'home',
          name: 'DesktopHome',
          component: () => import('@/modules/首页/pages/首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/home'), blogView: 'feed' },
        },
        {
          path: 'home/archive',
          name: 'DesktopBlogArchive',
          component: () => import('@/modules/首页/pages/首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/home'), blogView: 'archive' },
        },
        {
          path: 'home/announcements',
          name: 'DesktopBlogAnnouncements',
          component: () => import('@/modules/首页/pages/首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/home'), blogView: 'announcements' },
        },
        {
          path: 'home/blog/:slug',
          name: 'DesktopBlogArticleDetail',
          component: () => import('@/modules/首页/pages/首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/home'), keepAlive: true, preserveTabOnNavigate: true, blogView: 'feed' },
        },
        {
          path: 'home/moments/:momentId',
          name: 'DesktopBlogMomentDetail',
          component: () => import('@/modules/首页/pages/首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/home'), keepAlive: true, preserveTabOnNavigate: true, blogView: 'feed' },
        },
        {
          path: 'todos',
          name: 'DesktopTodos',
          component: () => import('@personal-system/module-todos').then((module) => module.TodosPage),
          meta: { title: 获取桌面路由标题('/todos') },
        },
        {
          path: 'memos',
          name: 'DesktopMemos',
          component: () => import('@personal-system/module-memos').then((module) => module.MemosPage),
          meta: { title: 获取桌面路由标题('/memos') },
        },
        {
          path: 'materials',
          name: 'DesktopCollections',
          component: () => import('@personal-system/module-materials').then((module) => module.MaterialsPage),
          meta: { title: 获取桌面路由标题('/materials') },
        },
        {
          path: 'articles',
          name: 'DesktopArticles',
          component: () => import('@personal-system/module-articles').then((module) => module.ArticlesPage),
          meta: { title: 获取桌面路由标题('/articles') },
        },
        {
          path: 'articles/edit/:id?',
          name: 'DesktopArticleEditor',
          component: () => import('@personal-system/module-articles').then((module) => module.ArticleEditorPage),
          meta: { title: 获取桌面路由标题('/articles'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'files',
          name: 'DesktopFiles',
          component: () => import('@personal-system/module-files').then((module) => module.FilesPage),
          meta: { title: 获取桌面路由标题('/files'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'bills',
          name: 'DesktopBills',
          component: () => import('@personal-system/module-bills').then((module) => module.BillsPage),
          meta: { title: 获取桌面路由标题('/bills') },
        },
        {
          path: 'moments',
          name: 'DesktopMoments',
          component: () => import('@personal-system/module-moments').then((module) => module.MomentsPage),
          meta: { title: 获取桌面路由标题('/moments'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools',
          name: 'DesktopTools',
          component: () => import('@/modules/工具/pages/工具首页页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools') },
        },
        {
          path: 'tools/image',
          name: 'DesktopImageTools',
          component: () => import('@personal-system/module-tools').then((module) => module.ImageToolsPage),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/image'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools/windows',
          name: 'DesktopWindowsTools',
          component: () => import('@/modules/工具/pages/Windows工具页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/windows'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'tools/image-classifier',
          name: 'DesktopImageClassifier',
          component: () => import('@/modules/工具/pages/图片分类页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/image-classifier'), keepAlive: true },
        },
        {
          path: 'tools/minecraft-server',
          name: 'DesktopMinecraftServerQuery',
          component: () => import('@/modules/工具/pages/MC服务器查询页面.vue'),
          meta: { requiresAuth: false, title: 获取桌面路由标题('/tools/minecraft-server'), keepAlive: true, preserveTabOnNavigate: true },
        },
        {
          path: 'device-sessions',
          name: 'DesktopDeviceSessions',
          component: () => import('@/modules/认证/pages/设备页面.vue'),
          meta: { title: 获取桌面路由标题('/device-sessions') },
        },
        {
          path: 'profile',
          name: 'DesktopProfile',
          component: () => import('@personal-system/module-profile').then((module) => module.ProfilePage),
          props: {
            sessionEndRedirect: { path: '/home' },
            onSessionEnded: () => 使用桌面标签存储().reset('/home'),
          },
          meta: { title: 获取桌面路由标题('/profile') },
        },
        {
          path: 'settings',
          name: 'DesktopSettings',
          component: () => import('@/modules/设置/pages/设置页面.vue'),
          meta: { title: 获取桌面路由标题('/settings') },
        },
        {
          path: 'settings/api-environment',
          name: 'DesktopSettingsApiEnvironment',
          component: () => import('@/modules/设置/pages/接口环境页面.vue'),
          meta: { title: '接口环境' },
        },
      ],
    },
    ...收集模块路由(desktopModules),
    {
      path: '/:pathMatch(.*)*',
      redirect: '/home',
    },
  ],
})

注册标准认证守卫(router, () => 使用认证存储(), {
  loginRouteName: 'DesktopLogin',
  authenticatedRouteName: 'DesktopHome',
  handleUnauthorizedRoute: (to) => {
    使用登录门禁存储().open({ redirectPath: to.fullPath })
  },
})

export default router
