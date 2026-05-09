<template>
  <RouterView />
  <DesktopLoginDialog />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import DesktopLoginDialog from '@/modules/auth/components/DesktopLoginDialog.vue'
</script>
