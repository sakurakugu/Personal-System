<script setup lang="ts">
import { MagicStick, PictureFilled } from '@element-plus/icons-vue'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/AppConsoleLayout.vue'
import type { 控制台菜单项 } from '../components/layout/console-layout'

const menuItems: 控制台菜单项[] = [
  { label: '图片编辑', key: '/tools', icon: PictureFilled },
  { label: '更多工具', key: '/tools/more', icon: MagicStick, disabled: true },
]
</script>

<template>
  <AppConsoleLayout
    title="所有工具"
    storage-key="tools_sider_mode"
    :menu-items="menuItems"
  >
    <RouterView />
  </AppConsoleLayout>
</template>
