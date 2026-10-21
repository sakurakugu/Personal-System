import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    consoleView?: boolean
    requiresAuth?: boolean
    blogView?: string
    /** 页面标题，用于控制台标签页标题与可读性展示。 */
    title?: string
    searchPlaceholder?: string
    searchTarget?: 'current' | 'blog'
  }
}
