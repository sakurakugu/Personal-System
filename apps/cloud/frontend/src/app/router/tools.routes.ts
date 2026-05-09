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
        component: () => import('@personal-system/module-tools').then((module) => module.ToolsPage),
      },
      {
        path: 'image',
        name: 'ImageToolsPage',
        component: () => import('@personal-system/module-tools').then((module) => module.ImageToolsPage),
      },
    ],
  },
  {
    path: '/tools/image-editor',
    redirect: '/tools/image',
  },
]
