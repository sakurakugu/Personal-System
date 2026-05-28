<script setup lang="ts">
import { 过滤工具侧栏菜单项 } from '@personal-system/module-tools'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/应用控制台布局.vue'

const auth = 使用认证存储()
const menuItems = computed(() => 过滤工具侧栏菜单项({
  isAuthenticated: auth.isAuthenticated,
}))
</script>

<template>
  <AppConsoleLayout
    title="所有工具"
    storage-key="tools_sider_mode"
    :menu-items="menuItems"
  >
    <RouterView v-slot="{ Component }">
      <component
        :is="Component"
        :show-authenticated-tools="auth.isAuthenticated"
      />
    </RouterView>
  </AppConsoleLayout>
</template>
