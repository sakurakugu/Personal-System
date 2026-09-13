<script setup lang="ts">
import { 过滤工具侧栏菜单项 } from '../../modules/工具/src'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { 使用设置存储 } from '../../shared/stores/settings'
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import AppConsoleLayout from '../components/layout/应用控制台布局.vue'

const auth = 使用认证存储()
const settings = 使用设置存储()
const menuItems = computed(() => settings.toolsEnabled
  ? 过滤工具侧栏菜单项({ isAuthenticated: auth.isAuthenticated })
  : [])
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
