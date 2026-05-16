import type { RouteRecordRaw } from 'vue-router'

export const blogRoutes: RouteRecordRaw[] = [
  {
    path: '/blog',
    name: 'BlogHome',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'feed' },
  },
  {
    path: '/archive',
    name: 'BlogArchive',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'archive' },
  },
  {
    path: '/announcements',
    name: 'BlogAnnouncements',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'announcements' },
  },
  {
    path: '/friends',
    name: 'BlogFriends',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'friends' },
  },
  {
    path: '/about',
    name: 'BlogAbout',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'about' },
  },
  {
    path: '/guestbook',
    name: 'BlogGuestbook',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'guestbook' },
  },
  {
    path: '/sponsor',
    name: 'BlogSponsor',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'sponsor' },
  },
  {
    path: '/bangumi',
    name: 'BlogBangumi',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'bangumi' },
  },
  {
    path: '/gallery',
    name: 'BlogGallery',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'gallery' },
  },
  {
    path: '/rss',
    name: 'BlogRss',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'rss' },
  },
  {
    path: '/blog/:slug',
    name: 'ArticleDetail',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
  },
  {
    path: '/moments/:momentId',
    name: 'MomentDetail',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'feed' },
  },
]
