<script setup lang="ts">
import { ConsoleSidebarLayout } from '@personal-system/ui'
import type { 控制台菜单项 } from './console-layout'

defineProps<{
  title: string
  storageKey: string
  menuItems: 控制台菜单项[]
}>()
</script>

<template>
  <ConsoleSidebarLayout
    :title="title"
    :storage-key="storageKey"
    :menu-items="menuItems"
    layout-class="console-layout"
    sider-class="console-sider"
    main-base-class="console-main"
  >
    <slot />
  </ConsoleSidebarLayout>
</template>

<style scoped>
.console-layout {
  height: calc(var(--app-viewport-height) - var(--app-header-height));
}

.console-main {
  --dashboard-panel-radius: 12px;
}

.console-main :deep(> *) {
  border-radius: var(--dashboard-panel-radius);
  overflow: hidden;
}

.dark .console-sider {
  background-color: var(--sidebar-bg) !important;
  border-right-color: var(--border-color) !important;
}

.dark .console-sider :deep(.ps-console-sider__title) {
  color: var(--text-primary);
}

.dark .console-sider :deep(.ps-sidebar-handle__trigger:hover) {
  background-color: var(--bg-hover) !important;
}

.dark .console-sider.is-hidden :deep(.ps-sidebar-handle__trigger) {
  background-color: color-mix(in srgb, var(--sidebar-bg) 88%, #ffffff 12%);
  border-color: var(--border-color);
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.32);
}

.dark .console-sider :deep(.ps-console-sider__resizer::before) {
  background: var(--border-color);
}

.dark .console-main {
  background-color: var(--bg-primary);
}
</style>
