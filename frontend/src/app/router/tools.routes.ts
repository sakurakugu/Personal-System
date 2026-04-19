import type { RouteRecordRaw } from 'vue-router'

export const toolsRoutes: RouteRecordRaw[] = [
  {
    path: '/tools',
    name: 'ToolsPage',
    component: () => import('../../modules/tools/pages/ToolsPage.vue'),
  },
  {
    path: '/tools/image-editor',
    redirect: '/tools',
  },
]
