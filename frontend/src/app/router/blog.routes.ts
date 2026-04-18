import type { RouteRecordRaw } from 'vue-router'

export const blogRoutes: RouteRecordRaw[] = [
  {
    path: '/blog',
    name: 'BlogHome',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'feed' },
  },
  {
    path: '/archive',
    name: 'BlogArchive',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'archive' },
  },
  {
    path: '/announcements',
    name: 'BlogAnnouncements',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'announcements' },
  },
  {
    path: '/friends',
    name: 'BlogFriends',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'friends' },
  },
  {
    path: '/about',
    name: 'BlogAbout',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'about' },
  },
  {
    path: '/sponsor',
    name: 'BlogSponsor',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'sponsor' },
  },
  {
    path: '/bangumi',
    name: 'BlogBangumi',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'bangumi' },
  },
  {
    path: '/gallery',
    name: 'BlogGallery',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'gallery' },
  },
  {
    path: '/rss',
    name: 'BlogRss',
    component: () => import('../../views/blog/BlogHome.vue'),
    meta: { blogView: 'rss' },
  },
  {
    path: '/blog/:slug',
    name: 'ArticleDetail',
    component: () => import('../../views/blog/BlogHome.vue'),
  },
]
