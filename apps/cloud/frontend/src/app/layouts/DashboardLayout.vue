<script setup lang="ts">
import { useAuthStore } from '@personal-system/domain/auth'
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/AppConsoleLayout.vue'
import type { 控制台菜单项 } from '../components/layout/console-layout'
import { 过滤仪表盘菜单项 } from '../navigation/dashboard-navigation'

const auth = useAuthStore()

const menuOptions = computed<控制台菜单项[]>(() => 过滤仪表盘菜单项({
  isAdmin: auth.isAdmin,
  isSuperAdmin: auth.isSuperAdmin,
}))
</script>

<template>
  <AppConsoleLayout
    title="控制台"
    storage-key="dashboard_sider_mode"
    :menu-items="menuOptions"
  >
    <RouterView />
  </AppConsoleLayout>
</template>
