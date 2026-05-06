import type { RouteRecordRaw } from 'vue-router'

export interface AppModule {
  id: string
  routes?: RouteRecordRaw[]
}

export function collectModuleRoutes(modules: readonly AppModule[]): RouteRecordRaw[] {
  return modules.flatMap((module) => module.routes ?? [])
}
