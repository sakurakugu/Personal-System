<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  icon?: Component
}>()
</script>

<template>
  <div class="settings-page-shell">
    <h2 class="settings-page-shell__title">
      <component :is="icon" v-if="icon" class="settings-page-shell__title-icon" />
      <span>{{ title }}</span>
    </h2>

    <slot />
  </div>
</template>

<style scoped>
.settings-page-shell {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.settings-page-shell__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 24px;
  font-size: 24px;
  line-height: 1.2;
}

.settings-page-shell__title-icon {
  width: 1em;
  height: 1em;
}
</style>
