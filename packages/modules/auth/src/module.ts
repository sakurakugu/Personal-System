import type { AppModule } from '@personal-system/app-core'
import type { RouteComponent, RouteMeta, RouteRecordRaw, RouteRecordNameGeneric } from 'vue-router'

export interface AuthModuleOptions {
  id?: string
  loginComponent: RouteComponent
  loginPath: string
  loginRouteName: RouteRecordNameGeneric
  loginRouteMeta?: RouteMeta
  routes?: RouteRecordRaw[]
}

export function createAuthModule(options: AuthModuleOptions): AppModule {
  return {
    id: options.id ?? 'auth',
    routes: [
      {
        path: options.loginPath,
        name: options.loginRouteName,
        component: options.loginComponent,
        meta: { guestOnly: true, ...(options.loginRouteMeta ?? {}) },
      },
      ...(options.routes ?? []),
    ],
  }
}
