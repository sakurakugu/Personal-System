import type { RouteLocationNormalizedLoaded } from 'vue-router'

export function 判断是否控制台路由(route: RouteLocationNormalizedLoaded) {
  return route.matched.some((record) => record.meta.consoleView === true)
}
