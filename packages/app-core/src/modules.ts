import type { RouteRecordRaw } from 'vue-router'

export interface AppModule {
  id: string
  routes?: RouteRecordRaw[]
}

export function 收集模块路由(modules: readonly AppModule[]): RouteRecordRaw[] {
  return modules.flatMap((module) => module.routes ?? [])
}
