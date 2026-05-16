<script setup lang="ts">
import { 使用认证存储 } from '@personal-system/domain/auth'
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/应用控制台布局.vue'
import type { 控制台菜单项 } from '../components/layout/ConsoleLayout'
import { 过滤仪表盘菜单项 } from '../navigation/dashboard-navigation'

const auth = 使用认证存储()

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
