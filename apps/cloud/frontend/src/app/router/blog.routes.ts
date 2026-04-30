import type { RouteRecordRaw } from 'vue-router'

export const blogRoutes: RouteRecordRaw[] = [
  {
    path: '/blog',
    name: 'BlogHome',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'feed' },
  },
  {
    path: '/archive',
    name: 'BlogArchive',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'archive' },
  },
  {
    path: '/announcements',
    name: 'BlogAnnouncements',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'announcements' },
  },
  {
    path: '/friends',
    name: 'BlogFriends',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'friends' },
  },
  {
    path: '/about',
    name: 'BlogAbout',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'about' },
  },
  {
    path: '/guestbook',
    name: 'BlogGuestbook',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'guestbook' },
  },
  {
    path: '/sponsor',
    name: 'BlogSponsor',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'sponsor' },
  },
  {
    path: '/bangumi',
    name: 'BlogBangumi',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'bangumi' },
  },
  {
    path: '/gallery',
    name: 'BlogGallery',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'gallery' },
  },
  {
    path: '/rss',
    name: 'BlogRss',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'rss' },
  },
  {
    path: '/blog/:slug',
    name: 'ArticleDetail',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
  },
  {
    path: '/moments/:momentId',
    name: 'MomentDetail',
    component: () => import('../../modules/blog/pages/BlogHome.vue'),
    meta: { blogView: 'feed' },
  },
]
