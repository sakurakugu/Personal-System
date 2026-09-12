import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    consoleView?: boolean
    requiresAuth?: boolean
    blogView?: string
    searchPlaceholder?: string
    searchTarget?: 'current' | 'blog'
  }
}
