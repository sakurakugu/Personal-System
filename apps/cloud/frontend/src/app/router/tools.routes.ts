import type { RouteRecordRaw } from 'vue-router'

export const toolsRoutes: RouteRecordRaw[] = [
  {
    path: '/tools',
    component: () => import('../layouts/ToolsLayout.vue'),
    meta: { consoleView: true },
    children: [
      {
        path: '',
        name: 'ToolsPage',
        component: () => import('@personal-system/modules/tools').then((module) => module.ToolsPage),
      },
    ],
  },
  {
    path: '/tools/image-editor',
    redirect: '/tools',
  },
]
