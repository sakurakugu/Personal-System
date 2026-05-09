<script setup lang="ts">
import PhoneLoginDialog from '@/modules/auth/components/PhoneLoginDialog.vue'
import AppTabBar from '@/shared/components/AppTabBar.vue'
import { useTabBarStore } from '@/shared/stores/tab-bar'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const tabBar = useTabBarStore()
tabBar.init()

const showTabBar = computed(() => route.meta.hideTabBar !== true)
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
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}
</style>
