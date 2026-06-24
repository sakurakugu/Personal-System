import type { RouteRecordRaw } from 'vue-router'

export const blogRoutes: RouteRecordRaw[] = [
  {
    path: '/blog',
    name: 'BlogHome',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'feed', searchPlaceholder: '搜索文章...', searchTarget: 'current' },
  },
  {
    path: '/archive',
    name: 'BlogArchive',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'archive', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
  },
  {
    path: '/announcements',
    name: 'BlogAnnouncements',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'announcements', searchPlaceholder: '搜索公告...', searchTarget: 'current' },
  },
  {
    path: '/friends',
    name: 'BlogFriends',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'friends', searchPlaceholder: '搜索友链', searchTarget: 'current' },
  },
  {
    path: '/about',
    name: 'BlogAbout',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'about', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
  },
  {
    path: '/guestbook',
    name: 'BlogGuestbook',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'guestbook', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
  },
  {
    path: '/sponsor',
    name: 'BlogSponsor',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'sponsor', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
  },
  {
    path: '/media',
    name: 'BlogMedia',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'media', searchPlaceholder: '搜索文娱作品', searchTarget: 'current' },
  },
  {
    path: '/gallery',
    name: 'BlogGallery',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'gallery', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
  },
  {
    path: '/rss',
    name: 'BlogRss',
    component: () => import('../../modules/博客/pages/博客首页.vue'),
    meta: { blogView: 'rss', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
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
    meta: { blogView: 'feed', searchPlaceholder: '搜索文章...', searchTarget: 'blog' },
  },
]
