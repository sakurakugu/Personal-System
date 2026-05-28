<script setup lang="ts">
import PhoneLoginDialog from '@/modules/认证/components/手机登录弹窗.vue'
import AppTabBar from '@/shared/components/标签栏.vue'
import { 使用标签栏存储 } from '@/shared/stores/tab-bar'
import { 是否为应用标签页ID } from '@/shared/tab-bar'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const tabBar = 使用标签栏存储()
tabBar.init()

const showTabBar = computed(() => {
  const tabBarId = route.meta.tabBarId
  if (是否为应用标签页ID(tabBarId)) {
    return tabBar.visibleTabIds.includes(tabBarId)
  }
  return route.meta.hideTabBar !== true
})
const tabs = computed(() => tabBar.visibleTabs)
</script>

<template>
  <div class="shell">
    <main class="shell-main">
      <RouterView />
    </main>

    <AppTabBar v-if="showTabBar" :items="tabs" />
    <PhoneLoginDialog />
  </div>
</template>

<style scoped>
.shell {
  height: var(--app-viewport-height);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.shell-main {
  flex: 1;
  min-height: 0;
  max-width: 100%;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}
</style>
