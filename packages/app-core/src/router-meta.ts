import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    blogView?: string
    consoleView?: boolean
    guestOnly?: boolean
    hideTabBar?: boolean
    requiresAdmin?: boolean
    requiresAuth?: boolean
    requiresSuperAdmin?: boolean
  }
}

export {}
