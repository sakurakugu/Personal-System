<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { to: '/', label: '首页' },
  { to: '/todos', label: '待办' },
  { to: '/me', label: '我的' },
]

const showTabBar = computed(() => route.meta.hideTabBar !== true)
</script>

<template>
  <div class="shell">
    <main class="shell-main">
      <RouterView />
    </main>

    <nav v-if="showTabBar" class="tabbar">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        class="tabbar-link"
        active-class="tabbar-link--active"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>
  </div>
</template>
