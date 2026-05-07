<script setup lang="ts">
import { 工具侧栏菜单项 } from '@personal-system/modules/tools'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/AppConsoleLayout.vue'
</script>

<template>
  <AppConsoleLayout
    title="所有工具"
    storage-key="tools_sider_mode"
    :menu-items="工具侧栏菜单项"
  >
    <RouterView />
  </AppConsoleLayout>
</template>
