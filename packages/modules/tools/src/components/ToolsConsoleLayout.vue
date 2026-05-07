<script setup lang="ts">
import { ConsoleSidebarLayout } from '@personal-system/ui'
import type { 工具菜单项 } from '../console-layout'

defineProps<{
  title: string
  storageKey: string
  menuItems: 工具菜单项[]
  mainClass?: string
}>()
</script>

<template>
  <ConsoleSidebarLayout
    :title="title"
    :storage-key="storageKey"
    :menu-items="menuItems"
    :main-class="mainClass"
    layout-class="tools-console-layout"
    sider-class="tools-console-sider"
    main-base-class="tools-console-main"
  >
    <slot />
  </ConsoleSidebarLayout>
</template>

<style scoped>
.tools-console-layout {
  height: 100%;
}

.tools-console-main {
  --dashboard-panel-radius: 12px;
}

.tools-console-main :deep(.el-card) {
  border-radius: var(--dashboard-panel-radius);
  overflow: hidden;
}

.dark .tools-console-sider {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color, var(--el-border-color)) !important;
}

.dark .tools-console-sider :deep(.ps-console-sider__title) {
  color: var(--text-primary, var(--el-text-color-primary));
}

.dark .tools-console-sider :deep(.ps-sidebar-handle__trigger:hover) {
  background-color: var(--bg-hover, rgb(255 255 255 / 0.04)) !important;
}

.dark .tools-console-sider.is-hidden :deep(.ps-sidebar-handle__trigger) {
  background-color: color-mix(in srgb, var(--sidebar-bg) 88%, #ffffff 12%);
  border-color: var(--border-color, var(--el-border-color));
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.32);
}

.dark .tools-console-sider :deep(.ps-console-sider__resizer::before) {
  background: var(--border-color, var(--el-border-color));
}
</style>
