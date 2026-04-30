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
        component: () => import('../../modules/tools/pages/ToolsPage.vue'),
      },
    ],
  },
  {
    path: '/tools/image-editor',
    redirect: '/tools',
  },
]
