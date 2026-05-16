import type { RouteLocationNormalizedLoaded } from 'vue-router'

export const BLOG_VIEW_MODES = [
  'feed',
  'archive',
  'announcements',
  'friends',
  'about',
  'guestbook',
  'sponsor',
  'bangumi',
  'gallery',
  'rss',
] as const

export type BlogViewMode = typeof BLOG_VIEW_MODES[number]
export type BlogSortMode = 'comprehensive' | 'latest' | 'hot'

const BLOG_ROUTE_NAME_BY_VIEW: Record<BlogViewMode, string> = {
  feed: 'BlogHome',
  archive: 'BlogArchive',
  announcements: 'BlogAnnouncements',
  friends: 'BlogFriends',
  about: 'BlogAbout',
  guestbook: 'BlogGuestbook',
  sponsor: 'BlogSponsor',
  bangumi: 'BlogBangumi',
  gallery: 'BlogGallery',
  rss: 'BlogRss',
}

export interface BlogFeedQueryState {
  search: string
  category: string | null
  sort: BlogSortMode
}

export function isBlogViewMode(value: unknown): value is BlogViewMode {
  return typeof value === 'string' && (BLOG_VIEW_MODES as readonly string[]).includes(value)
}

export function resolveBlogViewMode(route: RouteLocationNormalizedLoaded): BlogViewMode {
  const routeView = route.meta.blogView
  if (isBlogViewMode(routeView)) {
    return routeView
  }
  return 'feed'
}

export function getBlogRouteName(view: BlogViewMode): string {
  return BLOG_ROUTE_NAME_BY_VIEW[view]
}

export function buildBlogFeedQuery(state: BlogFeedQueryState): Record<string, string> | undefined {
  const query: Record<string, string> = {}

  if (state.search) {
    query.search = state.search
  }
  if (state.category) {
    query.category = state.category
  }
  if (state.sort !== 'comprehensive') {
    query.sort = state.sort
  }

  return Object.keys(query).length > 0 ? query : undefined
}

export function parseBlogFeedQuery(route: RouteLocationNormalizedLoaded): BlogFeedQueryState {
  const search = typeof route.query.search === 'string' ? route.query.search : ''
  const category = typeof route.query.category === 'string' ? route.query.category : null
  const sort = route.query.sort === 'latest' || route.query.sort === 'hot'
    ? route.query.sort
    : 'comprehensive'

  return {
    search,
    category,
    sort,
  }
}
