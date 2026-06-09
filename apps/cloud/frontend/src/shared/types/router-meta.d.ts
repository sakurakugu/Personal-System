import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    consoleView?: boolean
    requiresAuth?: boolean
    requiresAdmin?: boolean
    requiresSuperAdmin?: boolean
    blogView?: string
    searchPlaceholder?: string
    searchTarget?: 'current' | 'blog'
  }
}
