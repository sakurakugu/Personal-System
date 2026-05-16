<template>
  <RouterView />
  <DesktopLoginDialog />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import DesktopLoginDialog from '@/modules/认证/components/DesktopLoginDialog.vue'
</script>
