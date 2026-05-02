<script setup lang="ts">
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
  <div class="shell" :class="{ 'shell--with-tabbar': showTabBar }">
    <main class="shell-main">
      <RouterView />
    </main>

    <AppTabBar v-if="showTabBar" :items="tabs" />
  </div>
</template>

<style scoped>
.shell {
  min-height: var(--app-viewport-height);
  display: flex;
  flex-direction: column;
}

.shell-main {
  flex: 1;
  min-height: 0;
}

.shell--with-tabbar .shell-main {
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}
</style>
