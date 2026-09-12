import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    blogView?: string
    consoleView?: boolean
    guestOnly?: boolean
    hideTabBar?: boolean
    tabBarId?: string
    requiresAuth?: boolean
  }
}

export {}
