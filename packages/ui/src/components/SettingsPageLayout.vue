<script setup lang="ts">
import type { Component } from 'vue'
import PageSectionShell from './PageSectionShell.vue'

defineProps<{
  title: string
  icon?: Component
}>()
</script>

<template>
  <div class="settings-page-layout">
    <PageSectionShell :title="title" :icon="icon">
      <slot />
    </PageSectionShell>
  </div>
</template>

<style scoped>
.settings-page-layout {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}
</style>
