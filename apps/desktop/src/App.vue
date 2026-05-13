<template>
  <RouterView />
  <DesktopLoginDialog v-if="showLoginDialog" />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useRoute } from 'vue-router'
import DesktopLoginDialog from '@/modules/auth/components/DesktopLoginDialog.vue'

const route = useRoute()
const isWidgetRoute = computed(() => route.path.startsWith('/widget'))
const showLoginDialog = computed(() => !isWidgetRoute.value)

watch(
  isWidgetRoute,
  (visible) => {
    document.body.classList.toggle('desktop-widget-body', visible)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  document.body.classList.remove('desktop-widget-body')
})
</script>
